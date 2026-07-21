from pathlib import Path

from webpage_translation.qa.types import BBox, Finding, PageResult, TextItem
from webpage_translation.report.data import build_payload
from webpage_translation.report.render import render_report


def _payload(tmp: Path) -> dict:
    shot = tmp / "shot.png"
    shot.write_bytes(b"\x89PNG\r\n\x1a\n")
    page = PageResult(
        name="homepage",
        url="https://x",
        timestamp="t",
        texts=(TextItem("Search", "#s", BBox(10, 20, 30, 40)),),
        screenshot=shot,
        error=None,
    )
    findings = (Finding("homepage", "Search", "#s", "en", "th", 0.9),)
    return build_payload([(page, findings)], locale="th-TH", date="2026-08-31")


def test_render_creates_dir_and_index(tmp_path: Path):
    out = tmp_path / "report" / "20260721-100000"
    index = render_report(out, _payload(tmp_path))
    assert index == out / "index.html"
    assert index.exists()
    body = index.read_text(encoding="utf-8")
    assert "homepage" in body
    assert "th-TH" in body
    assert "Search" in body
    assert "left:10px" in body
    assert "top:20px" in body
    assert (out / "screenshots" / "shot.png").exists()


def test_render_refuses_existing_dir(tmp_path: Path):
    out = tmp_path / "report" / "20260721-100000"
    out.mkdir(parents=True)
    try:
        render_report(out, _payload(tmp_path))
    except FileExistsError:
        return
    raise AssertionError("expected FileExistsError")


def test_render_handles_missing_screenshot(tmp_path: Path):
    page = PageResult(
        name="results",
        url="https://y",
        timestamp="t",
        texts=(),
        screenshot=None,
        error=None,
    )
    payload = build_payload([(page, ())], locale="th-TH", date="2026-08-31")
    out = tmp_path / "report" / "20260721-100001"
    index = render_report(out, payload)
    assert "no screenshot" in index.read_text(encoding="utf-8").lower()
