from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from webpage_translation.context import FlowContext
from webpage_translation.driver import booking_form, fare_option, flight_search, homepage
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.qa.checker import check_page
from webpage_translation.qa.types import Finding, PageResult
from webpage_translation.report.data import build_payload, write_json
from webpage_translation.report.render import render_report


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="webpage-translation")
    p.add_argument("--locale", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--report-root", default="./reports")
    return p.parse_args(argv)


def _run_flow(
    browser: Browser, ctx: FlowContext
) -> list[tuple[PageResult, tuple[Finding, ...]]]:
    steps: list[PageResult] = []
    home = homepage.open_and_set_locale(browser, ctx)
    steps.append(home)
    if home.error is None:
        steps.append(flight_search.search(browser, ctx))
        steps.append(fare_option.pick_first_fare(browser, ctx))
        steps.append(booking_form.reach_guest_form(browser, ctx))
    return [(page, check_page(page, ctx.locale)) for page in steps]


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
        results_out = _run_flow(browser, ctx)
    except BrowserError as exc:
        logging.error("browser error: %s", exc)
        return 2
    payload = build_payload(results_out, locale=args.locale, date=args.date)
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
