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
