from __future__ import annotations

from datetime import UTC, date, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult, TextItem

_MAX_MONTH_CLICKS = 24


def _click_by_name(browser: Browser, needle: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if 'backendDOMNodeId' in n and n.get('name', {{}}).get('value', '').find({needle!r}) >= 0)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
    )
    browser.run(script)


def _type_into(browser: Browser, placeholder_needle: str, value: str) -> None:
    script = (
        f"js('document.querySelectorAll(\"input\").forEach(el => {{ if (el.placeholder && el.placeholder.indexOf({placeholder_needle!r}) >= 0) el.focus(); }})')\n"
        f"type_text({value!r})\n"
    )
    browser.run(script)


def _navigate_calendar_to(browser: Browser, target: date) -> None:
    target_month = target.strftime("%Y-%m")
    for _ in range(_MAX_MONTH_CLICKS):
        header = browser.eval_json(
            "js('document.querySelector(\"[data-testid=calendar-header]\")?.innerText || \"\"')"
        )
        if isinstance(header, str) and target_month in header:
            return
        _click_by_name(browser, "Next month")
    raise BrowserError(f"calendar could not reach {target}")


def search(
    browser: Browser,
    ctx: FlowContext,
    *,
    origin: str = "SIN",
    dest: str = "SHA",
    one_way: bool = True,
) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "flight_search.png"
    url = "https://www.traveloka.com/flight"
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        _click_by_name(browser, "Flights")
        _type_into(browser, "From", origin)
        _click_by_name(browser, origin)
        _type_into(browser, "To", dest)
        _click_by_name(browser, dest)
        if one_way:
            _click_by_name(browser, "One Way")
        target = datetime.fromisoformat(ctx.date).date()
        _navigate_calendar_to(browser, target)
        _click_by_name(browser, target.strftime("%d %B %Y"))
        _click_by_name(browser, "Search Flights")
        browser.wait_for_load()
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
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
