from __future__ import annotations

import json

from webpage_translation.driver.browser import Browser


def wait_for_selector(browser: Browser, selector: str, timeout: float = 15) -> None:
    script = f"wait_for_element({selector!r}, timeout={timeout})\n"
    browser.run(script)


def click_first(browser: Browser, selector: str) -> None:
    sel_js = json.dumps(selector)
    snippet = f"document.querySelector({sel_js}).click()"
    script = f"js({json.dumps(snippet)})\n"
    browser.run(script)
