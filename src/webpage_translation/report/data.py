from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from webpage_translation.qa.types import Finding, PageResult


def build_payload(
    results: Sequence[tuple[PageResult, tuple[Finding, ...]]],
    *,
    locale: str,
    date: str,
) -> dict[str, Any]:
    return {
        "meta": {
            "locale": locale,
            "date": date,
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "pages": [
            {
                "page": page.to_dict(),
                "findings": [f.to_dict() for f in findings],
            }
            for page, findings in results
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
