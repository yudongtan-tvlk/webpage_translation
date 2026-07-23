from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from webpage_translation.context import FlowContext
from webpage_translation.driver import (
    booking_form,
    fare_option,
    flight_card_tabs,
    flight_search,
    homepage,
)
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.qa.checker import check_page, normalize_locale
from webpage_translation.qa.gemini_review import GeminiReview, load_api_key, review_page
from webpage_translation.qa.types import Finding, PageResult
from webpage_translation.report.data import build_payload, write_json
from webpage_translation.report.render import render_report


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="webpage-translation")
    p.add_argument("--locale", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--report-root", default="./reports")
    p.add_argument(
        "--gemini-review",
        action="store_true",
        help="Also send each screenshot to Gemini Flash for a native-quality review.",
    )
    p.add_argument(
        "--tabs-only",
        action="store_true",
        help=(
            "Only report the 4 in-card tab pages (flight_details, "
            "fare_benefits, refund, reschedule). Homepage and flight_search "
            "still run for navigation but are not written to the report."
        ),
    )
    return p.parse_args(argv)


def _run_flow(
    browser: Browser, ctx: FlowContext, *, tabs_only: bool = False
) -> list[tuple[PageResult, tuple[Finding, ...]]]:
    steps: list[PageResult] = []
    home = homepage.open_and_set_locale(browser, ctx)
    if not tabs_only:
        steps.append(home)
    if home.error is None:
        fs = flight_search.search(browser, ctx)
        if not tabs_only:
            steps.append(fs)
        steps.extend(flight_card_tabs.scrape_all_tabs(browser, ctx))
        if not tabs_only:
            steps.append(fare_option.pick_first_fare(browser, ctx))
            steps.append(booking_form.reach_guest_form(browser, ctx))
    elif tabs_only:
        # Homepage failed but we still need to surface that in the report.
        steps.append(home)
    return [(page, check_page(page, ctx.locale)) for page in steps]


def _gemini_reviews(
    results_out: list[tuple[PageResult, tuple[Finding, ...]]],
    *,
    locale: str,
) -> list[GeminiReview]:
    api_key = load_api_key()
    if api_key is None:
        logging.warning(
            "gemini-review requested but no GEMINI_KEY / GEMINI_API_KEY found "
            "(and no src/webpage_translation/.env)"
        )
        return []
    if normalize_locale(locale) == "en":
        logging.info("skipping gemini-review: locale is English")
        return []
    reviews: list[GeminiReview] = []
    for page, _ in results_out:
        if page.screenshot is None or not page.screenshot.exists():
            continue
        try:
            review = review_page(
                page_name=page.name,
                screenshot=page.screenshot,
                locale=locale,
                api_key=api_key,
            )
        except Exception as exc:
            logging.error("gemini-review failed for %s: %s", page.name, exc)
            continue
        logging.info(
            "gemini-review [%s] score=%s english_present=%s",
            page.name,
            review.quality_score,
            review.english_present,
        )
        reviews.append(review)
    return reviews


def cli(argv: Sequence[str] | None = None) -> int:
    args = _parse(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    slug = f"{args.locale}-{stamp}"
    report_root = Path(args.report_root)
    report_dir = report_root / slug
    ctx = FlowContext(
        locale=args.locale,
        date=args.date,
        screenshots_dir=report_root / f"{slug}-captures",
    )
    try:
        browser = Browser()
        # Reachability probe — first real subprocess call
        browser.run("print('probe')")
    except BrowserError as exc:
        logging.error("browser init failed: %s", exc)
        print("hint: run `browser-use --doctor`")
        return 2
    try:
        results_out = _run_flow(browser, ctx, tabs_only=args.tabs_only)
    except BrowserError as exc:
        logging.error("browser error: %s", exc)
        return 2
    reviews: list[GeminiReview] = []
    if args.gemini_review:
        reviews = _gemini_reviews(results_out, locale=args.locale)
    payload = build_payload(
        results_out, locale=args.locale, date=args.date, gemini_reviews=reviews
    )
    render_report(report_dir, payload)
    write_json(report_dir / "data.json", payload)
    findings_total = sum(len(f) for _, f in results_out)
    flow_broken = any(p.error is not None for p, _ in results_out)
    print(
        f"{len(results_out)} pages, {findings_total} findings — see {report_dir / 'index.html'}"
    )
    if flow_broken:
        return 3
    return 1 if findings_total > 0 else 0


def main() -> None:
    raise SystemExit(cli())
