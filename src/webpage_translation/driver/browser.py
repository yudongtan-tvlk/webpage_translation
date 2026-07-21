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

    def screenshot(self, path: Path) -> None:
        script = (
            "import base64, pathlib\n"
            "data = cdp('Page.captureScreenshot', format='png')['data']\n"
            f"pathlib.Path({str(path)!r}).write_bytes(base64.b64decode(data))\n"
        )
        self.run(script)
