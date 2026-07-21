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
        flight_search,
        homepage,
        results,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage"))
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: _mk("flight_search"))
    monkeypatch.setattr(results, "pick_first", lambda b, c: _mk("results"))
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: _mk("booking_form"))
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", lambda: object())  # noqa: E731


def test_cli_returns_0_when_no_findings(stub_driver: None, tmp_path: Path):
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 0


def test_cli_returns_3_and_stops_when_homepage_broken(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_search,
        homepage,
        results,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage", error="boom"))
    called: list[str] = []
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: called.append("fs") or _mk("flight_search"))
    monkeypatch.setattr(results, "pick_first", lambda b, c: called.append("r") or _mk("results"))
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: called.append("fo") or _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: called.append("bf") or _mk("booking_form"))
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", lambda: object())  # noqa: E731
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 3
    assert called == []  # downstream steps never invoked
