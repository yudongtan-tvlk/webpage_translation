import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from webpage_translation.context import FlowContext
from webpage_translation.driver.booking_form import reach_guest_form
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.fare_option import pick_first_fare
from webpage_translation.driver.flight_search import search


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "1", reason="set RUN_E2E=1 to enable"
)


def test_fare_and_booking_th(tmp_path: Path) -> None:
    target = (date.today() + timedelta(days=45)).isoformat()
    ctx = FlowContext(locale="th-TH", date=target, screenshots_dir=tmp_path)
    browser = Browser()

    fs = search(browser, ctx)
    assert fs.error is None, fs.error

    fo = pick_first_fare(browser, ctx)
    assert fo.error is None, fo.error
    assert fo.screenshot is not None and fo.screenshot.exists()
    assert len(fo.texts) > 20

    bf = reach_guest_form(browser, ctx)
    assert bf.error is None, bf.error
    assert bf.screenshot is not None and bf.screenshot.exists()
    assert len(bf.texts) > 20
