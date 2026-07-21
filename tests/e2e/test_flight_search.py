import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.flight_search import search


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "1", reason="set RUN_E2E=1 to enable"
)


def test_flight_search_th_returns_results(tmp_path: Path) -> None:
    target = (date.today() + timedelta(days=45)).isoformat()
    ctx = FlowContext(locale="th-TH", date=target, screenshots_dir=tmp_path)
    result = search(Browser(), ctx)
    assert result.name == "flight_search"
    assert result.error is None, result.error
    assert result.screenshot is not None and result.screenshot.exists()
    assert len(result.texts) > 20, f"only {len(result.texts)} texts scraped"
    joined = " ".join(t.text for t in result.texts)
    assert "SIN" in joined or "Singapore" in joined or "สิงคโปร์" in joined
    assert "SHA" in joined or "Shanghai" in joined or "เซี่ยงไฮ้" in joined
