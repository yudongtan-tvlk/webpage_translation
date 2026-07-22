from __future__ import annotations

import json
import re
from importlib.resources import files

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^[A-Z]{2,3}$"),
    re.compile(r"^[A-Z0-9]{2}\s?\d+$"),
    re.compile(r"^[\d.,]+$"),
    re.compile(r"^[¥$€£฿₫]\s?[\d.,]+$"),
    re.compile(r"^Rp\s?[\d.,]+$"),
    # ISO 4217 3-letter code + digits, e.g. "THB 4,989.16", "SGD 12", "USD 1,207.00"
    re.compile(r"^[A-Z]{3}\s+[\d.,]+$"),
    # No-space prefix, e.g. "VND799.468", "USD100".
    re.compile(r"^[A-Z]{3}[\d.,]+$"),
    # ISO code + price with locale-native "per unit" tail.
    re.compile(r"^[A-Z]{3}\s+[\d.,]+\s*/\s*\S+$"),
    # Postfix currency, e.g. "3.997.340 VND", "12.958.821 VND".
    re.compile(r"^[\d.,]+\s+[A-Z]{3}$"),
    # Price range: "THB 5,002.84 - THB 39,842.88".
    re.compile(r"^[A-Z]{3}\s+[\d.,]+\s*-\s*[A-Z]{3}\s+[\d.,]+$"),
    # Postfix-currency price range: "3.933.514 VND - 28.025.869 VND".
    re.compile(r"^[\d.,]+\s+[A-Z]{3}\s*-\s*[\d.,]+\s+[A-Z]{3}$"),
    # Standalone alphanumeric promo codes (uppercase letters/digits, 4-32 chars).
    re.compile(r"^[A-Z0-9]{4,32}$"),
    # Locale/currency chip in header, e.g. "THB | TH", "SGD | EN".
    re.compile(r"^[A-Z]{3}\s*\|\s*[A-Z]{2}$"),
    # Stop-count labels, e.g. "1 stop", "2 stops", "2+ stops".
    re.compile(r"^\d+\+?\s+stops?$"),
)


def _load_brands() -> frozenset[str]:
    raw = files("webpage_translation.qa.data").joinpath("brands.json").read_text(encoding="utf-8")
    return frozenset(name.casefold() for name in json.loads(raw))


_BRANDS: frozenset[str] = _load_brands()


def is_allowlisted(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if any(p.match(stripped) for p in _PATTERNS):
        return True
    if stripped.casefold() in _BRANDS:
        return True
    return False
