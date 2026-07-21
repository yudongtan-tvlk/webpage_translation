from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import click_first, wait_for_selector
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult, TextItem


def pick_first_fare(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "fare_option.png"
    url = "https://www.traveloka.com/flight/fare-option"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    selector = "[data-testid=fare-card], [data-testid=fare-option-item]"
    try:
        wait_for_selector(browser, selector)
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
        click_first(browser, selector)
        browser.wait_for_load()
    except Exception as exc:
        error = f"fare_option failed: {exc}"
    return PageResult(
        name="fare_option",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
