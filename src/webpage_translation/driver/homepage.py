from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult, TextItem

_LOCALE_URLS: dict[str, str] = {
    "th-TH": "https://www.traveloka.com/th-th/",
    "id-ID": "https://www.traveloka.com/id-id/",
    "vi-VN": "https://www.traveloka.com/vi-vn/",
    "zh-CN": "https://www.traveloka.com/zh-cn/",
    "en-SG": "https://www.traveloka.com/en-sg/",
}


def _locale_url(locale: str) -> str | None:
    return _LOCALE_URLS.get(locale)


def open_and_set_locale(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "homepage.png"
    url = _locale_url(ctx.locale)
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    if url is None:
        error = f"unsupported locale: {ctx.locale}"
        url = "https://www.traveloka.com/"
    else:
        try:
            browser.new_tab(url)
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
