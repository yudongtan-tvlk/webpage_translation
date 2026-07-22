from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import wait_for_selector, wait_until_stable
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts, max_content_bottom
from webpage_translation.qa.types import PageResult, TextItem

_LOCALE_PATHS: dict[str, str] = {
    "th-TH": "th-th",
    "id-ID": "id-id",
    "vi-VN": "vi-vn",
    "zh-CN": "zh-cn",
    "en-SG": "en-sg",
    "ja-JP": "ja-jp",
    "ko-KR": "ko-kr",
    "ms-MY": "ms-my",
}


def _build_search_url(locale: str, origin: str, dest: str, iso_date: str) -> str:
    path = _LOCALE_PATHS.get(locale, "en-sg")
    d = datetime.fromisoformat(iso_date).date()
    date_param = d.strftime("%d-%m-%Y")
    return (
        f"https://www.traveloka.com/{path}/flight/fullsearch"
        f"?ap={origin}.{dest}&dt={date_param}.NA&ps=1.0.0&sc=ECONOMY"
    )


def search(
    browser: Browser,
    ctx: FlowContext,
    *,
    origin: str = "SIN",
    dest: str = "SHA",
    one_way: bool = True,  # noqa: ARG001 — one-way encoded in URL via ".NA"
) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "flight_search.png"
    url = _build_search_url(ctx.locale, origin, dest, ctx.date)
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        browser.new_tab(url)
        wait_for_selector(browser, "[data-testid^='flight-inventory-card-container']", timeout=30)
        wait_until_stable(
            browser,
            "[data-testid^='flight-inventory-card-container']",
            interval=0.8,
            stable_samples=4,
            timeout=30,
        )
        browser.hydrate_scroll()
        texts = extract_visible_texts(browser)
        browser.screenshot(shot, min_height=max_content_bottom(texts))
    except Exception as exc:
        error = f"flight_search failed: {exc}"
    return PageResult(
        name="flight_search",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
