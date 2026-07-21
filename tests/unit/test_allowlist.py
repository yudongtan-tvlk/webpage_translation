import pytest
from webpage_translation.qa.allowlist import is_allowlisted


@pytest.mark.parametrize("text", [
    "",
    "   ",
    "SIN",
    "SHA",
    "SQ 851",
    "MH370",
    "123",
    "1,234.56",
    "¥1234",
    "$99",
    "€10",
    "Rp 1.500.000",
    "฿250",
    "₫50000",
    "Traveloka",
    "traveloka",
    "VISA",
    "Mastercard",
])
def test_allowlisted(text: str) -> None:
    assert is_allowlisted(text) is True


@pytest.mark.parametrize("text", [
    "Cari penerbangan",
    "Search flights",
    "SQ 851 to Shanghai",
    "SIN to SHA",
    "Free wifi",
    "ค้นหาเที่ยวบิน",
])
def test_not_allowlisted(text: str) -> None:
    assert is_allowlisted(text) is False
