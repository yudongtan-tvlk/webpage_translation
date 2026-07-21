from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BBox:
    x: float
    y: float
    w: float
    h: float

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}


@dataclass(frozen=True, slots=True)
class TextItem:
    text: str
    selector: str
    bbox: BBox

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "selector": self.selector, "bbox": self.bbox.to_dict()}


@dataclass(frozen=True, slots=True)
class PageResult:
    name: str
    url: str
    timestamp: str
    texts: tuple[TextItem, ...]
    screenshot: Path | None
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "timestamp": self.timestamp,
            "texts": [t.to_dict() for t in self.texts],
            "screenshot": str(self.screenshot) if self.screenshot is not None else None,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class Finding:
    page: str
    text: str
    selector: str
    detected: str
    expected: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "text": self.text,
            "selector": self.selector,
            "detected": self.detected,
            "expected": self.expected,
            "confidence": self.confidence,
        }
