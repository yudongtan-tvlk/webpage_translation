from __future__ import annotations

from webpage_translation.driver.browser import Browser


def wait_for_selector(browser: Browser, selector: str, timeout: float = 15) -> None:
    script = f"wait_for_selector({selector!r}, timeout={timeout})\n"
    browser.run(script)


def click_first(browser: Browser, selector: str) -> None:
    script = f"js('document.querySelector({selector!r}).click()')\n"
    browser.run(script)
