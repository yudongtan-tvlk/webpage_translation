import json
from pathlib import Path

from webpage_translation.qa.types import BBox, Finding, PageResult, TextItem
from webpage_translation.report.data import build_payload, write_json


def _result() -> tuple[PageResult, tuple[Finding, ...]]:
    page = PageResult(
        name="homepage",
        url="https://traveloka.com",
        timestamp="2026-07-21T10:00:00",
        texts=(TextItem("Search", "#s", BBox(0, 0, 10, 10)),),
        screenshot=None,
        error=None,
    )
    findings = (Finding("homepage", "Search", "#s", "en", "th", 0.9),)
    return (page, findings)


def test_build_payload_has_meta_and_pages():
    payload = build_payload([_result()], locale="th-TH", date="2026-08-31")
    assert payload["meta"]["locale"] == "th-TH"
    assert payload["meta"]["date"] == "2026-08-31"
    assert "generated_at" in payload["meta"]
    assert len(payload["pages"]) == 1
    p = payload["pages"][0]
    assert p["page"]["name"] == "homepage"
    assert p["findings"][0]["detected"] == "en"


def test_write_json_roundtrip(tmp_path: Path):
    payload = build_payload([_result()], locale="th-TH", date="2026-08-31")
    out = tmp_path / "data.json"
    write_json(out, payload)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
