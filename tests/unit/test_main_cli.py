from pathlib import Path

import pytest

from webpage_translation.main import cli
from webpage_translation.qa.types import PageResult


def _mk(name: str, error: str | None = None) -> PageResult:
    return PageResult(
        name=name, url="u", timestamp="t", texts=(), screenshot=None, error=error
    )


@pytest.fixture
def stub_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_card_tabs,
        flight_search,
        homepage,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage"))
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: _mk("flight_search"))
    monkeypatch.setattr(flight_card_tabs, "scrape_all_tabs", lambda b, c: [])
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: _mk("booking_form"))
    class StubBrowser:
        def run(self, script: str) -> str:
            return ""
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", StubBrowser)  # noqa: E731


def test_cli_returns_0_when_no_findings(stub_driver: None, tmp_path: Path):
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 0


def test_cli_returns_3_and_stops_when_homepage_broken(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_card_tabs,
        flight_search,
        homepage,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage", error="boom"))
    called: list[str] = []
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: called.append("fs") or _mk("flight_search"))
    monkeypatch.setattr(flight_card_tabs, "scrape_all_tabs", lambda b, c: (called.append("tabs") or []))
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: called.append("fo") or _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: called.append("bf") or _mk("booking_form"))
    class StubBrowser:
        def run(self, script: str) -> str:
            return ""
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", StubBrowser)
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 3
    assert called == []  # downstream steps never invoked


def test_cli_returns_1_when_findings_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from webpage_translation.qa.types import BBox, TextItem
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_card_tabs,
        flight_search,
        homepage,
    )
    items = (TextItem(text="Search flights", selector="#s", bbox=BBox(0, 0, 1, 1)),)
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: PageResult(
        name="homepage", url="u", timestamp="t", texts=items, screenshot=None, error=None
    ))
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: PageResult(
        name="flight_search", url="u", timestamp="t", texts=items, screenshot=None, error=None
    ))
    monkeypatch.setattr(flight_card_tabs, "scrape_all_tabs", lambda b, c: [])
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: _mk("booking_form"))
    class StubBrowser:
        def run(self, script: str) -> str:
            return ""
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", StubBrowser)
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 1


def test_cli_returns_2_when_browser_probe_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from webpage_translation.driver.browser import BrowserError
    class FailingBrowser:
        def __init__(self) -> None:
            pass
        def run(self, script: str) -> str:
            raise BrowserError("boom")
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", FailingBrowser)
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 2
