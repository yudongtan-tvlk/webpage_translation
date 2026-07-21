from __future__ import annotations

import time
from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult

_LOCALE_LABELS: dict[str, str] = {
    "th-TH": "ไทย",
    "id-ID": "Bahasa Indonesia",
    "vi-VN": "Tiếng Việt",
    "zh-CN": "简体中文",
    "en-SG": "English",
}


def _click_ax_node_by_name(browser: Browser, name_substr: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if n.get('name', {{}}).get('value', '').find({name_substr!r}) >= 0 and 'backendDOMNodeId' in n)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
        "wait_for_load()\n"
    )
    browser.run(script)


def _switch_locale(browser: Browser, locale: str) -> None:
    label = _LOCALE_LABELS.get(locale)
    if label is None:
        raise BrowserError(f"unsupported locale: {locale}")
    _click_ax_node_by_name(browser, "IDR")
    _click_ax_node_by_name(browser, label)


def open_and_set_locale(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "homepage.png"
    url = "https://www.traveloka.com/"
    error: str | None = None
    texts: tuple = ()
    try:
        browser.new_tab(url)
        browser.wait_for_load()
        for attempt in (1, 2):
            try:
                _switch_locale(browser, ctx.locale)
                break
            except Exception as exc:
                if attempt == 2:
                    error = f"locale switch failed: {exc}"
                    break
                time.sleep(2)
        if error is None:
            browser.screenshot(shot)
            texts = extract_visible_texts(browser)
    except Exception as exc:
        error = f"homepage failed: {exc}"
    return PageResult(
        name="homepage",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
