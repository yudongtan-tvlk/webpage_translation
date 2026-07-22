from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import click_first, wait_for_selector, wait_until_stable
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts, max_content_bottom
from webpage_translation.qa.types import PageResult, TextItem


_FARE_BUTTON = "[data-testid='button_ticket_option_select_0']"
_BOOKING_FORM = "[data-testid='view_desktop-flight-booking-form']"


def pick_first_fare(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "fare_option.png"
    url = "https://www.traveloka.com/flight/fare-option"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        wait_for_selector(browser, _FARE_BUTTON, timeout=30)
        wait_until_stable(
            browser,
            "[data-testid^='button_ticket_option_select_']",
            interval=0.8,
            stable_samples=4,
            timeout=30,
        )
        browser.hydrate_scroll()
        texts = extract_visible_texts(browser)
        browser.screenshot(shot, min_height=max_content_bottom(texts))
        click_first(browser, _FARE_BUTTON)
        wait_for_selector(browser, _BOOKING_FORM, timeout=60)
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
