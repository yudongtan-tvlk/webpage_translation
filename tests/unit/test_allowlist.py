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
    # ISO 4217 code + price
    "THB 4,989.16",
    "USD 1,207.00",
    "SGD 12",
    "MYR 1,234.56",
    # ISO code + price with locale-native /unit suffix
    "THB 1,232.00/คน",
    "USD 100/pax",
    # Price ranges (prefix + postfix currency)
    "THB 5,002.84 - THB 39,842.88",
    "SGD 12 - SGD 24",
    "3.933.514 VND - 28.025.869 VND",
    # Postfix currency (Vietnamese style)
    "3.997.340 VND",
    "12.958.821 VND",
    # No-space prefix
    "VND799.468",
    "USD100",
    # Longer promo codes
    "VIKKIDIGITALBANKWEDJUL",
    # Stops
    "1 stop",
    "2 stops",
    "2+ stops",
    # locale/currency chip
    "THB | TH",
    "SGD | EN",
    # promo code
    "TRAVELSGFL",
    # airlines
    "China Eastern Airlines",
    "China Southern Airlines",
    "Shenzhen Airlines",
    "Spring Airlines",
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
    # Regular mixed-case English must NOT be swallowed by the promo-code regex.
    "Search",
    "SearchFlights",
    "New Deal",
    # ISO code without price should still be caught by the plain code regex,
    # but the ISO-code-plus-price regex must not match a code alone with no digits.
    "SGD USD",
])
def test_not_allowlisted(text: str) -> None:
    assert is_allowlisted(text) is False
