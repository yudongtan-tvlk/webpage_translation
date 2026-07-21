from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FlowContext:
    locale: str
    date: str
    screenshots_dir: Path
