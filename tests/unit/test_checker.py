from webpage_translation.qa.checker import check_page, normalize_locale
from webpage_translation.qa.types import BBox, PageResult, TextItem


def _page(*texts: str) -> PageResult:
    items = tuple(
        TextItem(text=t, selector=f"#n{i}", bbox=BBox(0, 0, 1, 1))
        for i, t in enumerate(texts)
    )
    return PageResult(
        name="p", url="u", timestamp="t", texts=items, screenshot=None, error=None
    )


def test_normalize_locale():
    assert normalize_locale("th-TH") == "th"
    assert normalize_locale("th") == "th"
    assert normalize_locale("zh-CN") == "zh"


def test_check_page_returns_empty_on_error():
    p = PageResult(
        name="p", url="u", timestamp="t", texts=(), screenshot=None, error="boom"
    )
    assert check_page(p, "th") == ()


def test_check_page_skips_allowlisted():
    p = _page("Traveloka", "SIN", "SQ 851", "¥1,000")
    assert check_page(p, "th") == ()


def test_check_page_flags_english_when_expecting_thai():
    p = _page("Search for flights to Shanghai now")
    findings = check_page(p, "th-TH")
    assert len(findings) == 1
    f = findings[0]
    assert f.detected == "en"
    assert f.expected == "th"
    assert f.confidence >= 0.5


def test_check_page_passes_matching_locale():
    p = _page("นี่คือประโยคภาษาไทยเกี่ยวกับเที่ยวบิน")
    assert check_page(p, "th-TH") == ()
