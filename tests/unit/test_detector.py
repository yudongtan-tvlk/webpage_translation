import pytest
from webpage_translation.qa.detector import detect, MIN_CONFIDENCE, SUPPORTED


def test_supported_includes_expected():
    for code in ["en", "id", "th", "vi", "zh"]:
        assert code in SUPPORTED


@pytest.mark.parametrize("text,expected", [
    ("This is an English sentence about flights.", "en"),
    ("Ini adalah kalimat Bahasa Indonesia tentang penerbangan.", "id"),
    ("นี่คือประโยคภาษาไทยเกี่ยวกับเที่ยวบิน", "th"),
    ("这是一句关于航班的中文句子。", "zh"),
    ("Đây là một câu tiếng Việt về chuyến bay.", "vi"),
])
def test_detect_confident(text: str, expected: str) -> None:
    code, conf = detect(text)
    assert code == expected
    assert conf >= MIN_CONFIDENCE


def test_detect_unknown_on_gibberish():
    code, conf = detect("")
    assert code == "unknown"
    assert conf == 0.0
