from pathlib import Path

import pytest

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.homepage import open_and_set_locale


@pytest.mark.browser
def test_homepage_switch_to_thai(tmp_path: Path):
    ctx = FlowContext(locale="th-TH", date="2026-08-31", screenshots_dir=tmp_path)
    result = open_and_set_locale(Browser(), ctx)
    assert result.name == "homepage"
    assert result.error is None
    assert result.screenshot is not None and result.screenshot.exists()
    assert any("ค้นหา" in t.text or "เที่ยว" in t.text for t in result.texts)
