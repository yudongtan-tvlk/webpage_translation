from pathlib import Path
from webpage_translation.qa.types import BBox, TextItem, PageResult, Finding


def test_bbox_to_dict():
    assert BBox(1, 2, 3, 4).to_dict() == {"x": 1, "y": 2, "w": 3, "h": 4}


def test_text_item_to_dict():
    item = TextItem(text="hi", selector="#a", bbox=BBox(0, 0, 10, 10))
    assert item.to_dict() == {
        "text": "hi",
        "selector": "#a",
        "bbox": {"x": 0, "y": 0, "w": 10, "h": 10},
    }


def test_page_result_to_dict_with_error():
    r = PageResult(
        name="homepage",
        url="https://x",
        timestamp="2026-07-21T10:00:00",
        texts=(),
        screenshot=None,
        error="boom",
    )
    d = r.to_dict()
    assert d["texts"] == []
    assert d["error"] == "boom"
    assert d["screenshot"] is None


def test_page_result_screenshot_serialized_as_str():
    r = PageResult(
        name="homepage",
        url="https://x",
        timestamp="t",
        texts=(),
        screenshot=Path("/tmp/a.png"),
        error=None,
    )
    assert r.to_dict()["screenshot"] == "/tmp/a.png"


def test_finding_to_dict():
    f = Finding(
        page="homepage",
        text="Search",
        selector="#s",
        detected="en",
        expected="th",
        confidence=0.9,
    )
    assert f.to_dict() == {
        "page": "homepage",
        "text": "Search",
        "selector": "#s",
        "detected": "en",
        "expected": "th",
        "confidence": 0.9,
    }
