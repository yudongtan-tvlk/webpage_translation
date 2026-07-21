from __future__ import annotations

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
        found = browser.eval_json(f"js('!!document.querySelector({sel!r})')")
        if found:
            return True
    return False


def _fill_input_by_placeholder(browser: Browser, needle: str, value: str) -> None:
    script = (
        f"js('for (const el of document.querySelectorAll(\"input\")) {{ if (el.placeholder && el.placeholder.toLowerCase().indexOf({needle.lower()!r}) >= 0) {{ el.focus(); break; }} }}')\n"
        f"type_text({value!r})\n"
    )
    browser.run(script)


def _click_ax_name(browser: Browser, needle: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if 'backendDOMNodeId' in n and n.get('name', {{}}).get('value', '').find({needle!r}) >= 0)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
    )
    browser.run(script)


def reach_guest_form(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "booking_form.png"
    url = "https://www.traveloka.com/flight/booking"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        if _detect_auth_wall(browser):
            error = "auth_wall_hit"
        else:
            _fill_input_by_placeholder(browser, "email", "test+qa@example.com")
            _fill_input_by_placeholder(browser, "phone", "+6591234567")
            _click_ax_name(browser, "Continue")
            browser.wait_for_load()
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
