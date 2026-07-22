from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import click_first, wait_for_selector, wait_until_stable
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts, max_content_bottom
from webpage_translation.qa.types import PageResult, TextItem


_CARD_BUTTON = "[data-testid='flight-inventory-card-button']"
_BUNDLE_TRAY = "[data-testid='bundle-summary-tray']"


def pick_first(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "results.png"
    url = "https://www.traveloka.com/flight/search"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        wait_for_selector(browser, _CARD_BUTTON, timeout=30)
        wait_until_stable(
            browser, _CARD_BUTTON, interval=0.8, stable_samples=4, timeout=30
        )
        browser.hydrate_scroll()
        texts = extract_visible_texts(browser)
        browser.screenshot(shot, min_height=max_content_bottom(texts))
        click_first(browser, _CARD_BUTTON)
        wait_for_selector(browser, _BUNDLE_TRAY, timeout=30)
    except Exception as exc:
        error = f"results failed: {exc}"
    return PageResult(
        name="results",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
