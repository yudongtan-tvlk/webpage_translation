import json
from pathlib import Path
from unittest.mock import patch

import pytest
from webpage_translation.driver.browser import Browser, BrowserError


@pytest.fixture
def browser(tmp_path: Path) -> Browser:
    return Browser(cwd=tmp_path)


def _fake_completed(stdout: str, returncode: int = 0):
    from subprocess import CompletedProcess
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_run_returns_stdout(browser: Browser):
    with patch("subprocess.run", return_value=_fake_completed("hello\n")) as m:
        out = browser.run("print('hello')")
    assert out == "hello\n"
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0][0] == "browser-use"
    assert kwargs["input"].startswith("print('hello')")


def test_run_raises_on_error(browser: Browser):
    with patch("subprocess.run", return_value=_fake_completed("", returncode=1)):
        with pytest.raises(BrowserError):
            browser.run("print('boom')")


def test_eval_json_parses(browser: Browser):
    payload = json.dumps({"ok": True})
    with patch.object(Browser, "run", return_value=payload + "\n"):
        assert browser.eval_json("{'ok': True}") == {"ok": True}
