from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class BrowserError(RuntimeError):
    pass


class Browser:
    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = cwd

    def run(self, script: str) -> str:
        completed = subprocess.run(
            ["browser-use"],
            input=script,
            capture_output=True,
            text=True,
            cwd=self._cwd,
            check=False,
        )
        if completed.returncode != 0:
            raise BrowserError(
                f"browser-use exit {completed.returncode}: {completed.stderr.strip()}"
            )
        return completed.stdout

    def eval_json(self, expr: str) -> Any:
        script = f"import json; print(json.dumps({expr}))"
        raw = self.run(script)
        for line in reversed(raw.strip().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        raise BrowserError(f"no JSON payload in stdout:\n{raw}")

    def new_tab(self, url: str) -> None:
        self.run(f"new_tab({url!r})\nwait_for_load()")

    def wait_for_load(self, timeout: float = 30) -> None:
        self.run(f"wait_for_load(timeout={timeout})")

    def screenshot(self, path: Path, min_height: float = 0.0) -> None:
        script = (
            "import base64, pathlib, time\n"
            "js('window.scrollTo(0, 0)')\n"
            "time.sleep(0.3)\n"
            "w = js('document.documentElement.scrollWidth')\n"
            "h = js('document.documentElement.scrollHeight')\n"
            f"h = max(float(h), {float(min_height)})\n"
            "clip = {'x': 0, 'y': 0, 'width': float(w), 'height': float(h), 'scale': 1}\n"
            "data = cdp('Page.captureScreenshot', format='png', "
            "captureBeyondViewport=True, fromSurface=True, clip=clip)['data']\n"
            f"pathlib.Path({str(path)!r}).write_bytes(base64.b64decode(data))\n"
        )
        self.run(script)

    def hydrate_scroll(self) -> None:
        script = (
            "import time\n"
            "js('window.scrollTo(0, 0)')\n"
            "prev = -1\n"
            "for i in range(30):\n"
            "    h = js('document.documentElement.scrollHeight')\n"
            "    if h == prev:\n"
            "        break\n"
            "    prev = h\n"
            "    js('window.scrollTo(0, document.documentElement.scrollHeight)')\n"
            "    time.sleep(0.6)\n"
            "js('window.scrollTo(0, 0)')\n"
            "time.sleep(0.4)\n"
        )
        self.run(script)
