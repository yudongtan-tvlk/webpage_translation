from __future__ import annotations

import json
from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult, TextItem


def _detect_auth_wall(browser: Browser) -> bool:
    selectors = [
        "input[type=password]",
        "[data-testid=login-form]",
        "[aria-label*='Sign in' i]",
    ]
    for sel in selectors:
        sel_js = json.dumps(sel)
        snippet = f"!!document.querySelector({sel_js})"
        found = browser.eval_json(f"js({json.dumps(snippet)})")
        if found:
            return True
    return False


def reach_guest_form(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "booking_form.png"
    url = "https://www.traveloka.com/flight/booking"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        if _detect_auth_wall(browser):
            error = "auth_wall_hit"
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
    except Exception as exc:
        error = f"booking_form failed: {exc}"
    return PageResult(
        name="booking_form",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
