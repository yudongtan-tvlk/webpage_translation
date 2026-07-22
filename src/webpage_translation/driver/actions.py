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


def wait_until_stable(
    browser: Browser,
    selector: str,
    *,
    interval: float = 0.8,
    stable_samples: int = 4,
    timeout: float = 30.0,
) -> None:
    """Wait until querySelectorAll(selector).length stops changing.

    Polls every `interval` seconds. When the count matches the previous
    `stable_samples` samples in a row, considers hydration complete.
    """
    sel_js = json.dumps(selector)
    script = (
        "import time\n"
        f"selector = {sel_js}\n"
        f"deadline = time.monotonic() + {float(timeout)}\n"
        f"needed = {int(stable_samples)}\n"
        "history = []\n"
        "while time.monotonic() < deadline:\n"
        "    count = js('document.querySelectorAll(' + repr(selector) + ').length')\n"
        "    history.append(count)\n"
        "    if len(history) >= needed and len(set(history[-needed:])) == 1 and history[-1] > 0:\n"
        "        break\n"
        f"    time.sleep({float(interval)})\n"
        "else:\n"
        "    raise RuntimeError(f'wait_until_stable timeout on {selector!r}: {history}')\n"
    )
    browser.run(script)
