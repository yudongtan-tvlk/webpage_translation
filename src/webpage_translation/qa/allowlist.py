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
    # Same with locale-native "per unit" tail — currency stays a proper noun.
    re.compile(r"^[A-Z]{3}\s+[\d.,]+\s*/\s*\S+$"),
    # Price range: "THB 5,002.84 - THB 39,842.88".
    re.compile(r"^[A-Z]{3}\s+[\d.,]+\s*-\s*[A-Z]{3}\s+[\d.,]+$"),
    # Standalone alphanumeric promo codes (uppercase letters/digits, 4-16 chars).
    re.compile(r"^[A-Z0-9]{4,16}$"),
    # Locale/currency chip in header, e.g. "THB | TH", "SGD | EN".
    re.compile(r"^[A-Z]{3}\s*\|\s*[A-Z]{2}$"),
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
