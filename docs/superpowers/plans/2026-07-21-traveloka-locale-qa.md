# Traveloka Locale QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a CLI that drives Traveloka's 5-step booking flow under a chosen non-English locale, extracts visible text from each page, flags language mismatches, and writes an HTML+JSON report with screenshots.

**Architecture:** Single Python 3.12 package `webpage_translation` in three non-cross-importing layers: `driver/` (browser-use automation, one module per PRD page), `qa/` (pure language-detection + allowlist + finding generator), `report/` (Jinja2 HTML + JSON dumper). A thin `main.py` orchestrator sequences the flow.

**Tech Stack:** Python 3.12, uv for env + entry points, `browser-use` CLI (already installed, CDP-attached to local Chrome), `lingua-language-detector`, `jinja2`, pytest + pytest-cov, ruff, mypy.

## Global Constraints

- Python 3.12 only; managed exclusively via `uv`. Never invoke bare `python`/`pip`.
- Package name: `webpage_translation`; installed console script: `webpage-translation`.
- No upward imports across layers: `driver` may import `qa` types only from `qa.types`; `qa` never imports `driver`; `report` may import `qa` types and `driver` types, but not the reverse.
- Confidence threshold for `qa.detector`: `MIN_CONFIDENCE = 0.5` (constant, no override).
- Report directory naming: `./report/<YYYYMMDD-HHMMSS>/`, never overwrite.
- Exit codes: `0` clean run with 0 findings, `1` clean run with >0 findings, `2` infrastructure error, `3` flow broke mid-run.
- Coverage floor on `qa/` and `report/`: 80% (measured via `pytest --cov`).
- `mypy --strict` clean on `qa/` and `report/`.
- `ruff check` clean on the whole package.
- All driver interactions go through `browser-use` heredoc invocation (`browser-use <<'PY' ... PY`) called via `subprocess`; never import `browser_use` as a Python library.
- Dummy passenger data only. Never log real PII. Booking form is never submitted.
- No `.git` in repo yet — Task 1 initializes it. Every task ends with a commit.

---

## File Structure

```
webpage_translation/
├── pyproject.toml
├── README.md                                (existing CLAUDE.md separate)
├── src/webpage_translation/
│   ├── __init__.py
│   ├── main.py                              orchestrator + CLI
│   ├── context.py                           FlowContext dataclass
│   ├── driver/
│   │   ├── __init__.py
│   │   ├── browser.py                       subprocess wrapper around browser-use
│   │   ├── actions.py                       shared browser actions (wait_for_selector, click_first)
│   │   ├── extract.py                       shared JS visible-text extractor
│   │   ├── homepage.py                      Task 5
│   │   ├── flight_search.py                 Task 6
│   │   ├── results.py                       Task 7
│   │   ├── fare_option.py                   Task 8
│   │   └── booking_form.py                  Task 9
│   ├── qa/
│   │   ├── __init__.py
│   │   ├── types.py                         PageResult, TextItem, Finding
│   │   ├── detector.py
│   │   ├── allowlist.py
│   │   ├── checker.py
│   │   └── data/brands.json
│   └── report/
│       ├── __init__.py
│       ├── data.py                          JSON dumper
│       ├── render.py                        Jinja2 orchestrator
│       └── templates/
│           ├── index.html.j2
│           └── page.html.j2
└── tests/
    ├── unit/
    │   ├── test_types.py
    │   ├── test_detector.py
    │   ├── test_allowlist.py
    │   ├── test_checker.py
    │   ├── test_report_data.py
    │   └── test_report_render.py
    ├── integration/
    │   ├── conftest.py
    │   ├── test_extract_visible_texts.py
    │   └── test_homepage_locale_switch.py
    ├── e2e/
    │   └── test_full_flow_th.py
    └── fixtures/
        ├── visible_hidden.html
        └── multilang_page.json
```

---

## Task 1: Project scaffolding + git init

**Files:**
- Create: `pyproject.toml`
- Create: `src/webpage_translation/__init__.py`
- Create: `.gitignore`
- Create: `.python-version`

**Interfaces:**
- Consumes: (none)
- Produces: uv-managed project with console script `webpage-translation = webpage_translation.main:cli`. Empty package importable.

- [ ] **Step 1: Verify git repo present**

Run:
```bash
git rev-parse --is-inside-work-tree
```

Expected: `true`. If not, run `git init -b main` first.

- [ ] **Step 2: Write `.gitignore`**

Create `.gitignore`:
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/
report/
dist/
build/
*.egg-info/
.python-version
```

- [ ] **Step 3: Write `.python-version`**

Create `.python-version`:
```
3.12
```

- [ ] **Step 4: Write `pyproject.toml`**

Create `pyproject.toml`:
```toml
[project]
name = "webpage-translation"
version = "0.1.0"
description = "Locale QA for traveloka.com booking flow"
requires-python = ">=3.12,<3.13"
dependencies = [
    "lingua-language-detector>=2.0.2",
    "jinja2>=3.1.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "mypy>=1.11",
]

[project.scripts]
webpage-translation = "webpage_translation.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/webpage_translation"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
files = ["src/webpage_translation/qa", "src/webpage_translation/report"]

[tool.pytest.ini_options]
addopts = "-ra --strict-markers"
testpaths = ["tests"]
markers = [
    "browser: requires a live Chrome + browser-use daemon (env RUN_BROWSER_TESTS=1)",
]
```

- [ ] **Step 5: Create empty package + placeholder `main.cli`**

Create `src/webpage_translation/__init__.py`:
```python
__version__ = "0.1.0"
```

Create `src/webpage_translation/main.py`:
```python
def cli() -> None:
    raise SystemExit("webpage-translation: not implemented yet")
```

- [ ] **Step 6: Install with uv and smoke-test**

Run:
```bash
uv sync --extra dev
uv run webpage-translation
```

Expected: prints `webpage-translation: not implemented yet` and exits non-zero.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore .python-version src/webpage_translation
git commit -m "chore: scaffold uv project + console script"
```

---

## Task 2: `qa.types` — shared dataclasses

**Files:**
- Create: `src/webpage_translation/qa/__init__.py`
- Create: `src/webpage_translation/qa/types.py`
- Create: `tests/unit/test_types.py`

**Interfaces:**
- Consumes: (none)
- Produces:
  - `class BBox` frozen dataclass: `x: float, y: float, w: float, h: float`
  - `class TextItem` frozen dataclass: `text: str, selector: str, bbox: BBox`
  - `class PageResult` frozen dataclass: `name: str, url: str, timestamp: str, texts: tuple[TextItem, ...], screenshot: pathlib.Path | None, error: str | None`
  - `class Finding` frozen dataclass: `page: str, text: str, selector: str, detected: str, expected: str, confidence: float`
  - All types support `.to_dict()` → JSON-serializable `dict`.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_types.py`:
```python
from pathlib import Path
from webpage_translation.qa.types import BBox, TextItem, PageResult, Finding


def test_bbox_to_dict():
    assert BBox(1, 2, 3, 4).to_dict() == {"x": 1, "y": 2, "w": 3, "h": 4}


def test_text_item_to_dict():
    item = TextItem(text="hi", selector="#a", bbox=BBox(0, 0, 10, 10))
    assert item.to_dict() == {
        "text": "hi",
        "selector": "#a",
        "bbox": {"x": 0, "y": 0, "w": 10, "h": 10},
    }


def test_page_result_to_dict_with_error():
    r = PageResult(
        name="homepage",
        url="https://x",
        timestamp="2026-07-21T10:00:00",
        texts=(),
        screenshot=None,
        error="boom",
    )
    d = r.to_dict()
    assert d["texts"] == []
    assert d["error"] == "boom"
    assert d["screenshot"] is None


def test_page_result_screenshot_serialized_as_str():
    r = PageResult(
        name="homepage",
        url="https://x",
        timestamp="t",
        texts=(),
        screenshot=Path("/tmp/a.png"),
        error=None,
    )
    assert r.to_dict()["screenshot"] == "/tmp/a.png"


def test_finding_to_dict():
    f = Finding(
        page="homepage",
        text="Search",
        selector="#s",
        detected="en",
        expected="th",
        confidence=0.9,
    )
    assert f.to_dict() == {
        "page": "homepage",
        "text": "Search",
        "selector": "#s",
        "detected": "en",
        "expected": "th",
        "confidence": 0.9,
    }
```

- [ ] **Step 2: Run test — verify it fails**

Run: `uv run pytest tests/unit/test_types.py -v`
Expected: `ModuleNotFoundError: No module named 'webpage_translation.qa'`

- [ ] **Step 3: Implement**

Create `src/webpage_translation/qa/__init__.py` (empty).

Create `src/webpage_translation/qa/types.py`:
```python
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
```

- [ ] **Step 4: Run tests — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_types.py -v
uv run mypy src/webpage_translation/qa/types.py
```
Expected: all tests PASS, mypy `Success: no issues found in 1 source file`.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/qa tests/unit/test_types.py
git commit -m "feat(qa): add BBox/TextItem/PageResult/Finding dataclasses"
```

---

## Task 3: `qa.allowlist` — regex + brand skip filter

**Files:**
- Create: `src/webpage_translation/qa/allowlist.py`
- Create: `src/webpage_translation/qa/data/brands.json`
- Create: `tests/unit/test_allowlist.py`

**Interfaces:**
- Consumes: (none)
- Produces:
  - `def is_allowlisted(text: str) -> bool`
  - Rules applied in order: pure whitespace → True; matches any regex in `_PATTERNS` → True; case-insensitive exact match against loaded brand set → True; else False.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_allowlist.py`:
```python
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
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_allowlist.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/qa/data/brands.json`:
```json
[
  "Traveloka",
  "Visa",
  "Mastercard",
  "AMEX",
  "American Express",
  "JCB",
  "PayPal",
  "Google",
  "Apple",
  "Singapore Airlines",
  "Scoot",
  "AirAsia",
  "Jetstar",
  "Malaysia Airlines",
  "Cathay Pacific",
  "China Eastern",
  "China Southern",
  "Air China"
]
```

Create `src/webpage_translation/qa/allowlist.py`:
```python
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
```

Also create `src/webpage_translation/qa/data/__init__.py` (empty) so `importlib.resources` sees the package.

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_allowlist.py -v
uv run mypy src/webpage_translation/qa/allowlist.py
```
Expected: all PASS, mypy clean.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/qa/allowlist.py src/webpage_translation/qa/data tests/unit/test_allowlist.py
git commit -m "feat(qa): add allowlist filter for brands/codes/prices"
```

---

## Task 4: `qa.detector` — lingua wrapper

**Files:**
- Create: `src/webpage_translation/qa/detector.py`
- Create: `tests/unit/test_detector.py`

**Interfaces:**
- Consumes: (none)
- Produces:
  - `MIN_CONFIDENCE: float = 0.5`
  - `SUPPORTED: tuple[str, ...]` — ISO 639-1 codes for `en, id, th, vi, zh, ja, ko, ms`.
  - `def detect(text: str) -> tuple[str, float]` — returns `("unknown", 0.0)` when detector returns None or confidence < `MIN_CONFIDENCE`; otherwise `(iso_code, confidence)`.
  - Detector is lazily built once and cached at module scope.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_detector.py`:
```python
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
    code, conf = detect("x")
    assert code == "unknown"
    assert conf == 0.0
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_detector.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/qa/detector.py`:
```python
from __future__ import annotations

from functools import cache

from lingua import Language, LanguageDetector, LanguageDetectorBuilder

MIN_CONFIDENCE: float = 0.5

_LANG_MAP: dict[Language, str] = {
    Language.ENGLISH: "en",
    Language.INDONESIAN: "id",
    Language.THAI: "th",
    Language.VIETNAMESE: "vi",
    Language.CHINESE: "zh",
    Language.JAPANESE: "ja",
    Language.KOREAN: "ko",
    Language.MALAY: "ms",
}

SUPPORTED: tuple[str, ...] = tuple(sorted(_LANG_MAP.values()))


@cache
def _detector() -> LanguageDetector:
    return (
        LanguageDetectorBuilder.from_languages(*_LANG_MAP.keys())
        .with_preloaded_language_models()
        .build()
    )


def detect(text: str) -> tuple[str, float]:
    stripped = text.strip()
    if not stripped:
        return ("unknown", 0.0)
    det = _detector()
    lang = det.detect_language_of(stripped)
    if lang is None:
        return ("unknown", 0.0)
    confidence = det.compute_language_confidence(stripped, lang)
    if confidence < MIN_CONFIDENCE:
        return ("unknown", 0.0)
    return (_LANG_MAP[lang], confidence)
```

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_detector.py -v
uv run mypy src/webpage_translation/qa/detector.py
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/qa/detector.py tests/unit/test_detector.py
git commit -m "feat(qa): add lingua-backed language detector wrapper"
```

---

## Task 5: `qa.checker` — page-level finding generator

**Files:**
- Create: `src/webpage_translation/qa/checker.py`
- Create: `tests/unit/test_checker.py`

**Interfaces:**
- Consumes: `qa.types.PageResult, TextItem, BBox, Finding`, `qa.allowlist.is_allowlisted`, `qa.detector.detect`.
- Produces:
  - `def normalize_locale(locale: str) -> str` — `"th-TH"` → `"th"`; passthrough for bare `"th"`.
  - `def check_page(page: PageResult, expected_locale: str) -> tuple[Finding, ...]`:
    - Empty tuple when `page.error is not None`.
    - For each `TextItem`, skip if `is_allowlisted(text)`; otherwise `detect(text)` and emit Finding if detected != normalized expected (including `"unknown"`).
    - Confidence for `unknown` findings recorded as `0.0`.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_checker.py`:
```python
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
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_checker.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/qa/checker.py`:
```python
from __future__ import annotations

from webpage_translation.qa.allowlist import is_allowlisted
from webpage_translation.qa.detector import detect
from webpage_translation.qa.types import Finding, PageResult


def normalize_locale(locale: str) -> str:
    return locale.split("-", 1)[0].lower()


def check_page(page: PageResult, expected_locale: str) -> tuple[Finding, ...]:
    if page.error is not None:
        return ()
    expected = normalize_locale(expected_locale)
    out: list[Finding] = []
    for item in page.texts:
        if is_allowlisted(item.text):
            continue
        detected, confidence = detect(item.text)
        if detected == expected:
            continue
        out.append(
            Finding(
                page=page.name,
                text=item.text,
                selector=item.selector,
                detected=detected,
                expected=expected,
                confidence=confidence,
            )
        )
    return tuple(out)
```

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_checker.py -v
uv run mypy src/webpage_translation/qa/checker.py
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/qa/checker.py tests/unit/test_checker.py
git commit -m "feat(qa): add page-level checker with allowlist + detector"
```

---

## Task 6: `report.data` — JSON dumper

**Files:**
- Create: `src/webpage_translation/report/__init__.py`
- Create: `src/webpage_translation/report/data.py`
- Create: `tests/unit/test_report_data.py`

**Interfaces:**
- Consumes: `qa.types.PageResult, Finding`.
- Produces:
  - `def build_payload(results: Sequence[tuple[PageResult, tuple[Finding, ...]]], *, locale: str, date: str) -> dict`
  - `def write_json(path: Path, payload: dict) -> None`
  - JSON structure:
    ```json
    {
      "meta": {"locale": "th-TH", "date": "2026-08-31", "generated_at": "..."},
      "pages": [
        {"page": <PageResult.to_dict()>, "findings": [<Finding.to_dict()>...]},
        ...
      ]
    }
    ```
  - `generated_at` uses `datetime.now(UTC).isoformat(timespec="seconds")`.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_report_data.py`:
```python
import json
from pathlib import Path

from webpage_translation.qa.types import BBox, Finding, PageResult, TextItem
from webpage_translation.report.data import build_payload, write_json


def _result() -> tuple[PageResult, tuple[Finding, ...]]:
    page = PageResult(
        name="homepage",
        url="https://traveloka.com",
        timestamp="2026-07-21T10:00:00",
        texts=(TextItem("Search", "#s", BBox(0, 0, 10, 10)),),
        screenshot=None,
        error=None,
    )
    findings = (Finding("homepage", "Search", "#s", "en", "th", 0.9),)
    return (page, findings)


def test_build_payload_has_meta_and_pages():
    payload = build_payload([_result()], locale="th-TH", date="2026-08-31")
    assert payload["meta"]["locale"] == "th-TH"
    assert payload["meta"]["date"] == "2026-08-31"
    assert "generated_at" in payload["meta"]
    assert len(payload["pages"]) == 1
    p = payload["pages"][0]
    assert p["page"]["name"] == "homepage"
    assert p["findings"][0]["detected"] == "en"


def test_write_json_roundtrip(tmp_path: Path):
    payload = build_payload([_result()], locale="th-TH", date="2026-08-31")
    out = tmp_path / "data.json"
    write_json(out, payload)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_report_data.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/report/__init__.py` (empty).

Create `src/webpage_translation/report/data.py`:
```python
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
```

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_report_data.py -v
uv run mypy src/webpage_translation/report/data.py
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/report tests/unit/test_report_data.py
git commit -m "feat(report): build + write JSON payload"
```

---

## Task 7: `report.render` — Jinja2 HTML report

**Files:**
- Create: `src/webpage_translation/report/render.py`
- Create: `src/webpage_translation/report/templates/index.html.j2`
- Create: `src/webpage_translation/report/templates/page.html.j2`
- Create: `tests/unit/test_report_render.py`

**Interfaces:**
- Consumes: payload from `report.data.build_payload`.
- Produces:
  - `def render_report(output_dir: Path, payload: dict) -> Path` — creates `output_dir` (must not pre-exist), writes `index.html`, copies screenshots into `output_dir/screenshots/` when `page.screenshot` set, returns path to `index.html`.
  - Overlay coords rendered as inline `<div style="position:absolute; left:{x}px; top:{y}px; width:{w}px; height:{h}px; outline:2px solid red;">` per finding on top of `<img class="page-screenshot">`.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_report_render.py`:
```python
from pathlib import Path

from webpage_translation.qa.types import BBox, Finding, PageResult, TextItem
from webpage_translation.report.data import build_payload
from webpage_translation.report.render import render_report


def _payload(tmp: Path) -> dict:
    shot = tmp / "shot.png"
    shot.write_bytes(b"\x89PNG\r\n\x1a\n")
    page = PageResult(
        name="homepage",
        url="https://x",
        timestamp="t",
        texts=(TextItem("Search", "#s", BBox(10, 20, 30, 40)),),
        screenshot=shot,
        error=None,
    )
    findings = (Finding("homepage", "Search", "#s", "en", "th", 0.9),)
    return build_payload([(page, findings)], locale="th-TH", date="2026-08-31")


def test_render_creates_dir_and_index(tmp_path: Path):
    out = tmp_path / "report" / "20260721-100000"
    index = render_report(out, _payload(tmp_path))
    assert index == out / "index.html"
    assert index.exists()
    body = index.read_text(encoding="utf-8")
    assert "homepage" in body
    assert "th-TH" in body
    assert "Search" in body
    assert "left:10px" in body
    assert "top:20px" in body
    assert (out / "screenshots" / "shot.png").exists()


def test_render_refuses_existing_dir(tmp_path: Path):
    out = tmp_path / "report" / "20260721-100000"
    out.mkdir(parents=True)
    try:
        render_report(out, _payload(tmp_path))
    except FileExistsError:
        return
    raise AssertionError("expected FileExistsError")


def test_render_handles_missing_screenshot(tmp_path: Path):
    page = PageResult(
        name="results",
        url="https://y",
        timestamp="t",
        texts=(),
        screenshot=None,
        error=None,
    )
    payload = build_payload([(page, ())], locale="th-TH", date="2026-08-31")
    out = tmp_path / "report" / "20260721-100001"
    index = render_report(out, payload)
    assert "no screenshot" in index.read_text(encoding="utf-8").lower()
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_report_render.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/report/templates/page.html.j2`:
```html
<section class="page-block">
  <h2>{{ p.page.name }}</h2>
  <p><a href="{{ p.page.url }}">{{ p.page.url }}</a> · {{ p.page.timestamp }}</p>
  {% if p.page.error %}
    <p class="error">Error: {{ p.page.error }}</p>
  {% endif %}
  <div class="screenshot-wrap" style="position:relative; display:inline-block;">
    {% if p.page.screenshot %}
      <img class="page-screenshot" src="screenshots/{{ p.page.screenshot | basename }}" alt="{{ p.page.name }} screenshot" />
      {% for f in p.findings %}
        {% set item = p.page.texts | selectattr("selector", "equalto", f.selector) | list | first %}
        {% if item %}
          <div title="{{ f.text }} (detected {{ f.detected }})"
               style="position:absolute; left:{{ item.bbox.x }}px; top:{{ item.bbox.y }}px; width:{{ item.bbox.w }}px; height:{{ item.bbox.h }}px; outline:2px solid red;"></div>
        {% endif %}
      {% endfor %}
    {% else %}
      <p><em>No screenshot captured.</em></p>
    {% endif %}
  </div>
  <table class="findings">
    <thead><tr><th>Text</th><th>Detected</th><th>Expected</th><th>Confidence</th><th>Selector</th></tr></thead>
    <tbody>
      {% for f in p.findings %}
        <tr>
          <td>{{ f.text }}</td>
          <td>{{ f.detected }}</td>
          <td>{{ f.expected }}</td>
          <td>{{ "%.2f" | format(f.confidence) }}</td>
          <td><code>{{ f.selector }}</code></td>
        </tr>
      {% else %}
        <tr><td colspan="5"><em>No findings.</em></td></tr>
      {% endfor %}
    </tbody>
  </table>
</section>
```

Create `src/webpage_translation/report/templates/index.html.j2`:
```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Traveloka Locale QA — {{ payload.meta.locale }}</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 2rem; }
  h1 { margin-bottom: 0.25rem; }
  section.page-block { margin-bottom: 3rem; border-top: 1px solid #ccc; padding-top: 1rem; }
  img.page-screenshot { max-width: 100%; height: auto; border: 1px solid #ddd; }
  table.findings { border-collapse: collapse; margin-top: 1rem; width: 100%; }
  table.findings th, table.findings td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
  .error { color: #b00020; font-weight: bold; }
</style>
</head>
<body>
<h1>Traveloka Locale QA</h1>
<p>Locale: <strong>{{ payload.meta.locale }}</strong> · Date: {{ payload.meta.date }} · Generated: {{ payload.meta.generated_at }}</p>
{% for p in payload.pages %}
  {% include "page.html.j2" %}
{% endfor %}
</body>
</html>
```

Create `src/webpage_translation/report/render.py`:
```python
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


def _basename(value: str | None) -> str:
    if not value:
        return ""
    return Path(value).name


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("webpage_translation.report", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
    )
    env.filters["basename"] = _basename
    return env


def render_report(output_dir: Path, payload: dict[str, Any]) -> Path:
    if output_dir.exists():
        raise FileExistsError(f"report dir already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    shots_dir = output_dir / "screenshots"
    shots_dir.mkdir()
    for page in payload["pages"]:
        shot = page["page"].get("screenshot")
        if shot:
            src = Path(shot)
            if src.exists():
                shutil.copy2(src, shots_dir / src.name)
    env = _env()
    html = env.get_template("index.html.j2").render(payload=payload)
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index
```

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_report_render.py -v
uv run mypy src/webpage_translation/report/render.py
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/report tests/unit/test_report_render.py
git commit -m "feat(report): render HTML report with screenshot overlays"
```

---

## Task 8: `driver.browser` — subprocess wrapper around `browser-use`

**Files:**
- Create: `src/webpage_translation/driver/__init__.py`
- Create: `src/webpage_translation/context.py`
- Create: `src/webpage_translation/driver/browser.py`
- Create: `tests/unit/test_browser_wrapper.py`

**Interfaces:**
- Consumes: `qa.types.BBox, TextItem`.
- Produces:
  - `class FlowContext` in `context.py`: `locale: str, date: str, screenshots_dir: Path`. Frozen slots dataclass.
  - `class Browser` in `driver/browser.py`:
    - `def run(self, script: str) -> str` — executes `browser-use <<'PY' ... PY` via `subprocess.run`, returns stdout, raises `BrowserError` on non-zero exit.
    - `def eval_json(self, expr: str) -> Any` — runs `print(json.dumps(<expr>))` inside browser-use, parses result. Used by everything downstream.
    - `def screenshot(self, path: Path) -> None` — saves current viewport PNG to `path` via CDP.
    - `def new_tab(self, url: str) -> None` and `def wait_for_load(self, timeout: float = 30) -> None` — thin passthroughs.
  - `class BrowserError(RuntimeError)`.

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_browser_wrapper.py`:
```python
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from webpage_translation.driver.browser import Browser, BrowserError


@pytest.fixture
def browser(tmp_path: Path) -> Browser:
    return Browser(cwd=tmp_path)


def _fake_completed(stdout: str, returncode: int = 0):
    from subprocess import CompletedProcess
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_run_returns_stdout(browser: Browser):
    with patch("subprocess.run", return_value=_fake_completed("hello\n")) as m:
        out = browser.run("print('hello')")
    assert out == "hello\n"
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0][0] == "browser-use"
    assert kwargs["input"].startswith("print('hello')")


def test_run_raises_on_error(browser: Browser):
    with patch("subprocess.run", return_value=_fake_completed("", returncode=1)):
        with pytest.raises(BrowserError):
            browser.run("print('boom')")


def test_eval_json_parses(browser: Browser):
    payload = json.dumps({"ok": True})
    with patch.object(Browser, "run", return_value=payload + "\n"):
        assert browser.eval_json("{'ok': True}") == {"ok": True}
```

- [ ] **Step 2: Run — verify fail**

Run: `uv run pytest tests/unit/test_browser_wrapper.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/driver/__init__.py` (empty).

Create `src/webpage_translation/context.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FlowContext:
    locale: str
    date: str
    screenshots_dir: Path
```

Create `src/webpage_translation/driver/browser.py`:
```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class BrowserError(RuntimeError):
    pass


class Browser:
    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = cwd

    def run(self, script: str) -> str:
        completed = subprocess.run(
            ["browser-use"],
            input=script,
            capture_output=True,
            text=True,
            cwd=self._cwd,
            check=False,
        )
        if completed.returncode != 0:
            raise BrowserError(
                f"browser-use exit {completed.returncode}: {completed.stderr.strip()}"
            )
        return completed.stdout

    def eval_json(self, expr: str) -> Any:
        script = f"import json; print(json.dumps({expr}))"
        raw = self.run(script)
        for line in reversed(raw.strip().splitlines()):
            line = line.strip()
            if line.startswith("{") or line.startswith("["):
                return json.loads(line)
        raise BrowserError(f"no JSON payload in stdout:\n{raw}")

    def new_tab(self, url: str) -> None:
        self.run(f"new_tab({url!r})\nwait_for_load()")

    def wait_for_load(self, timeout: float = 30) -> None:
        self.run(f"wait_for_load(timeout={timeout})")

    def screenshot(self, path: Path) -> None:
        script = (
            "import base64, pathlib\n"
            "data = cdp('Page.captureScreenshot', format='png')['data']\n"
            f"pathlib.Path({str(path)!r}).write_bytes(base64.b64decode(data))\n"
        )
        self.run(script)
```

- [ ] **Step 4: Run — verify pass + mypy**

Run:
```bash
uv run pytest tests/unit/test_browser_wrapper.py -v
uv run mypy src/webpage_translation/driver/browser.py src/webpage_translation/context.py
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/driver src/webpage_translation/context.py tests/unit/test_browser_wrapper.py
git commit -m "feat(driver): subprocess wrapper for browser-use + FlowContext"
```

---

## Task 9: `driver.extract` — visible-text extractor primitive

**Files:**
- Create: `src/webpage_translation/driver/extract.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/fixtures/visible_hidden.html`
- Create: `tests/integration/test_extract_visible_texts.py`

**Interfaces:**
- Consumes: `driver.browser.Browser`, `qa.types.BBox, TextItem`.
- Produces:
  - `EXTRACT_JS: str` — inline JavaScript source that returns a JSON array of `{text, selector, bbox: {x,y,w,h}}` for every visible text-bearing leaf element.
  - `def extract_visible_texts(browser: Browser) -> tuple[TextItem, ...]` — runs the JS via `browser.eval_json("js(EXTRACT_JS)")` and adapts the result into `TextItem`s.
  - Filter rules in JS: `getComputedStyle.visibility != 'hidden'` and `!= 'collapse'`, `display != 'none'`, `opacity > 0`, bounding rect width and height > 0, `textContent.trim()` non-empty, node is a leaf w.r.t. text (its own text nodes, not concatenated children).

- [ ] **Step 1: Write fixture + failing integration test**

Create `tests/fixtures/visible_hidden.html`:
```html
<!doctype html>
<html><head><meta charset="utf-8"><title>fixture</title></head>
<body>
  <p id="visible">Hello world</p>
  <p id="hidden" style="display:none;">Ghost text</p>
  <p id="invisible" style="visibility:hidden;">Invisible</p>
  <p id="tiny" style="width:0;height:0;overflow:hidden;">Tiny</p>
  <div id="wrapper"><span id="inner">Nested visible</span></div>
  <p id="aria" aria-label="Hidden aria only"></p>
</body></html>
```

Create `tests/integration/conftest.py`:
```python
import os
import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_BROWSER_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="set RUN_BROWSER_TESTS=1 to enable")
    for item in items:
        if "browser" in item.keywords:
            item.add_marker(skip)
```

Create `tests/integration/test_extract_visible_texts.py`:
```python
from pathlib import Path

import pytest

from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts


FIXTURE = Path(__file__).parent.parent / "fixtures" / "visible_hidden.html"


@pytest.mark.browser
def test_extract_only_returns_visible(tmp_path: Path):
    browser = Browser()
    browser.new_tab(FIXTURE.resolve().as_uri())
    items = extract_visible_texts(browser)
    texts = {i.text for i in items}
    assert "Hello world" in texts
    assert "Nested visible" in texts
    assert "Ghost text" not in texts
    assert "Invisible" not in texts
    assert "Tiny" not in texts
    assert "Hidden aria only" not in texts
```

- [ ] **Step 2: Run — verify fail**

Run: `RUN_BROWSER_TESTS=1 uv run pytest tests/integration/test_extract_visible_texts.py -v`
Expected: `ModuleNotFoundError` for `webpage_translation.driver.extract`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/driver/extract.py`:
```python
from __future__ import annotations

from typing import Any

from webpage_translation.driver.browser import Browser
from webpage_translation.qa.types import BBox, TextItem


EXTRACT_JS: str = r"""
(function () {
  function selectorFor(el) {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.nodeName.toLowerCase();
      if (el.classList && el.classList.length) part += '.' + [...el.classList].map(CSS.escape).join('.');
      const parent = el.parentElement;
      if (parent) {
        const sibs = [...parent.children].filter(c => c.nodeName === el.nodeName);
        if (sibs.length > 1) part += ':nth-of-type(' + (sibs.indexOf(el) + 1) + ')';
      }
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  function ownText(el) {
    let s = '';
    for (const n of el.childNodes) {
      if (n.nodeType === 3) s += n.nodeValue;
    }
    return s.replace(/\s+/g, ' ').trim();
  }
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  let node = walker.currentNode;
  while (node) {
    const text = ownText(node);
    if (text) {
      const style = getComputedStyle(node);
      if (style.display !== 'none' && style.visibility !== 'hidden' && style.visibility !== 'collapse' && parseFloat(style.opacity || '1') > 0) {
        const r = node.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
          out.push({
            text,
            selector: selectorFor(node),
            bbox: { x: r.x, y: r.y, w: r.width, h: r.height },
          });
        }
      }
    }
    node = walker.nextNode();
  }
  return out;
})()
"""


def extract_visible_texts(browser: Browser) -> tuple[TextItem, ...]:
    raw: list[dict[str, Any]] = browser.eval_json(f"js({EXTRACT_JS!r})")
    items: list[TextItem] = []
    for row in raw:
        b = row["bbox"]
        items.append(
            TextItem(
                text=str(row["text"]),
                selector=str(row["selector"]),
                bbox=BBox(x=float(b["x"]), y=float(b["y"]), w=float(b["w"]), h=float(b["h"])),
            )
        )
    return tuple(items)
```

- [ ] **Step 4: Run — verify pass**

Run: `RUN_BROWSER_TESTS=1 uv run pytest tests/integration/test_extract_visible_texts.py -v`
Expected: PASS. If Chrome CDP not attached, follow browser-use skill instructions to enable remote debugging.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/driver/extract.py tests/integration tests/fixtures
git commit -m "feat(driver): add visible-text DOM extractor"
```

---

## Task 10: `driver.homepage` — homepage open + locale switch

**Files:**
- Create: `src/webpage_translation/driver/homepage.py`
- Modify: `tests/integration/test_homepage_locale_switch.py` (new file)

**Interfaces:**
- Consumes: `driver.browser.Browser`, `driver.extract.extract_visible_texts`, `context.FlowContext`, `qa.types.PageResult`.
- Produces:
  - `def open_and_set_locale(browser: Browser, ctx: FlowContext) -> PageResult`.
  - Steps: `new_tab("https://www.traveloka.com/")`, `wait_for_load()`. Click currency/locale widget (via AX-tree lookup: role `button` whose name matches `/^\w{3}\s+·/` or contains `EN`/currency). Pick target locale by AX-name match derived from `ctx.locale` (map `th-TH`→"ไทย", `id-ID`→"Bahasa Indonesia", `vi-VN`→"Tiếng Việt", `zh-CN`→"简体中文"). `wait_for_load()`. Screenshot. Extract texts. Return PageResult (name `homepage`, screenshot path in `ctx.screenshots_dir/homepage.png`).
  - Retry logic: locale switch retried once with a 2s sleep on any exception. Second failure returns `PageResult(..., error=<msg>)`.

- [ ] **Step 1: Write failing integration test**

Create `tests/integration/test_homepage_locale_switch.py`:
```python
from pathlib import Path

import pytest

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.homepage import open_and_set_locale


@pytest.mark.browser
def test_homepage_switch_to_thai(tmp_path: Path):
    ctx = FlowContext(locale="th-TH", date="2026-08-31", screenshots_dir=tmp_path)
    result = open_and_set_locale(Browser(), ctx)
    assert result.name == "homepage"
    assert result.error is None
    assert result.screenshot is not None and result.screenshot.exists()
    assert any("ค้นหา" in t.text or "เที่ยวบิน" in t.text for t in result.texts)
```

- [ ] **Step 2: Run — verify fail**

Run: `RUN_BROWSER_TESTS=1 uv run pytest tests/integration/test_homepage_locale_switch.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/webpage_translation/driver/homepage.py`:
```python
from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult

_LOCALE_LABELS: dict[str, str] = {
    "th-TH": "ไทย",
    "id-ID": "Bahasa Indonesia",
    "vi-VN": "Tiếng Việt",
    "zh-CN": "简体中文",
    "en-SG": "English",
}


def _click_ax_node_by_name(browser: Browser, name_substr: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if n.get('name', {{}}).get('value', '').find({name_substr!r}) >= 0 and 'backendDOMNodeId' in n)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
        "wait_for_load()\n"
    )
    browser.run(script)


def _switch_locale(browser: Browser, locale: str) -> None:
    label = _LOCALE_LABELS.get(locale)
    if label is None:
        raise BrowserError(f"unsupported locale: {locale}")
    _click_ax_node_by_name(browser, "IDR")
    _click_ax_node_by_name(browser, label)


def open_and_set_locale(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "homepage.png"
    url = "https://www.traveloka.com/"
    error: str | None = None
    texts: tuple = ()
    try:
        browser.new_tab(url)
        browser.wait_for_load()
        for attempt in (1, 2):
            try:
                _switch_locale(browser, ctx.locale)
                break
            except Exception as exc:
                if attempt == 2:
                    error = f"locale switch failed: {exc}"
                    break
                time.sleep(2)
        if error is None:
            browser.screenshot(shot)
            texts = extract_visible_texts(browser)
    except Exception as exc:
        error = f"homepage failed: {exc}"
    return PageResult(
        name="homepage",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
```

- [ ] **Step 4: Run — verify pass**

Run: `RUN_BROWSER_TESTS=1 uv run pytest tests/integration/test_homepage_locale_switch.py -v`
Expected: PASS on a live Chrome with Traveloka reachable. Live selectors may need adjustment — record any tweak in the task's commit message.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/driver/homepage.py tests/integration/test_homepage_locale_switch.py
git commit -m "feat(driver): homepage open + locale switch"
```

---

## Task 11: `driver.flight_search` — search SIN → SHA on target date

**Files:**
- Create: `src/webpage_translation/driver/flight_search.py`

**Interfaces:**
- Consumes: `driver.browser.Browser`, `driver.extract.extract_visible_texts`, `context.FlowContext`, `qa.types.PageResult`.
- Produces:
  - `def search(browser: Browser, ctx: FlowContext, *, origin: str = "SIN", dest: str = "SHA", one_way: bool = True) -> PageResult` with `name="flight_search"`.
  - Steps: ensure Flights tab active (AX click on "Flights"/localized label). Click origin input, type `origin`, wait for autocomplete list, click first suggestion (AX-tree children of the autocomplete listbox). Same for `dest`. Ensure One Way is selected (AX toggle). Open calendar, navigate to month of `ctx.date` (bounded 24 forward clicks), click day matching `ctx.date`. Click Search. `wait_for_load()`. Screenshot to `ctx.screenshots_dir/flight_search.png`. Extract.
  - Error paths: autocomplete timeout, calendar overshoot → return PageResult with `error=<msg>`.

- [ ] **Step 1: Write implementation (no live integration test — costs real Chrome navigation; smoke covered by Task 15 e2e)**

Create `src/webpage_translation/driver/flight_search.py`:
```python
from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult

_MAX_MONTH_CLICKS = 24


def _click_by_name(browser: Browser, needle: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if 'backendDOMNodeId' in n and n.get('name', {{}}).get('value', '').find({needle!r}) >= 0)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
    )
    browser.run(script)


def _type_into(browser: Browser, placeholder_needle: str, value: str) -> None:
    script = (
        f"js('document.querySelectorAll(\"input\").forEach(el => {{ if (el.placeholder && el.placeholder.indexOf({placeholder_needle!r}) >= 0) el.focus(); }})')\n"
        f"type_text({value!r})\n"
    )
    browser.run(script)


def _navigate_calendar_to(browser: Browser, target: date) -> None:
    target_month = target.strftime("%Y-%m")
    for _ in range(_MAX_MONTH_CLICKS):
        header = browser.eval_json(
            "js('document.querySelector(\"[data-testid=calendar-header]\")?.innerText || \"\"')"
        )
        if isinstance(header, str) and target_month in header:
            return
        _click_by_name(browser, "Next month")
    raise BrowserError(f"calendar could not reach {target}")


def search(
    browser: Browser,
    ctx: FlowContext,
    *,
    origin: str = "SIN",
    dest: str = "SHA",
    one_way: bool = True,
) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "flight_search.png"
    url = "https://www.traveloka.com/flight"
    error: str | None = None
    texts: tuple = ()
    try:
        _click_by_name(browser, "Flights")
        _type_into(browser, "From", origin)
        _click_by_name(browser, origin)
        _type_into(browser, "To", dest)
        _click_by_name(browser, dest)
        if one_way:
            _click_by_name(browser, "One Way")
        target = datetime.fromisoformat(ctx.date).date()
        _navigate_calendar_to(browser, target)
        _click_by_name(browser, target.strftime("%d %B %Y"))
        _click_by_name(browser, "Search Flights")
        browser.wait_for_load()
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
    except Exception as exc:
        error = f"flight_search failed: {exc}"
    return PageResult(
        name="flight_search",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
```

- [ ] **Step 2: Type-check + ruff**

Run:
```bash
uv run ruff check src/webpage_translation/driver/flight_search.py
uv run mypy src/webpage_translation/driver/flight_search.py --ignore-missing-imports
```
Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add src/webpage_translation/driver/flight_search.py
git commit -m "feat(driver): flight search SIN->SHA on target date"
```

---

## Task 12: `driver.actions` + `driver.results` + `driver.fare_option` — shared helpers + pick first everything

**Files:**
- Create: `src/webpage_translation/driver/actions.py`
- Create: `src/webpage_translation/driver/results.py`
- Create: `src/webpage_translation/driver/fare_option.py`

**Interfaces:**
- Produces:
  - `def wait_for_selector(browser: Browser, selector: str, timeout: float = 15) -> None` in `actions.py`.
  - `def click_first(browser: Browser, selector: str) -> None` in `actions.py`.
  - `def pick_first(browser: Browser, ctx: FlowContext) -> PageResult` — waits for `[data-testid=flight-card]` (or fallback), scrapes current page (name `results`), then clicks first card.
  - `def pick_first_fare(browser: Browser, ctx: FlowContext) -> PageResult` — waits for fare-option list (`[data-testid=fare-card]` or fallback), scrapes (name `fare_option`), clicks first fare option.
  - Both handle waits with 15s timeout and record `error` on timeout.

- [ ] **Step 1: Implement `driver/actions.py`**

```python
from __future__ import annotations

from webpage_translation.driver.browser import Browser


def wait_for_selector(browser: Browser, selector: str, timeout: float = 15) -> None:
    script = f"wait_for_selector({selector!r}, timeout={timeout})\n"
    browser.run(script)


def click_first(browser: Browser, selector: str) -> None:
    script = f"js('document.querySelector({selector!r}).click()')\n"
    browser.run(script)
```

- [ ] **Step 2: Implement `driver/results.py`**

```python
from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import click_first, wait_for_selector
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult


def pick_first(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "results.png"
    url = "https://www.traveloka.com/flight/search"
    error: str | None = None
    texts: tuple = ()
    selector = "[data-testid=flight-card], [data-testid=flight-search-result-item]"
    try:
        wait_for_selector(browser, selector)
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
        click_first(browser, selector)
        browser.wait_for_load()
    except Exception as exc:
        error = f"results failed: {exc}"
    return PageResult(
        name="results",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
```

- [ ] **Step 3: Implement `driver/fare_option.py`**

```python
from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import click_first, wait_for_selector
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult


def pick_first_fare(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "fare_option.png"
    url = "https://www.traveloka.com/flight/fare-option"
    error: str | None = None
    texts: tuple = ()
    selector = "[data-testid=fare-card], [data-testid=fare-option-item]"
    try:
        wait_for_selector(browser, selector)
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
        click_first(browser, selector)
        browser.wait_for_load()
    except Exception as exc:
        error = f"fare_option failed: {exc}"
    return PageResult(
        name="fare_option",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
```

- [ ] **Step 4: Type-check + ruff**

Run:
```bash
uv run ruff check src/webpage_translation/driver/actions.py src/webpage_translation/driver/results.py src/webpage_translation/driver/fare_option.py
uv run mypy src/webpage_translation/driver/actions.py src/webpage_translation/driver/results.py src/webpage_translation/driver/fare_option.py --ignore-missing-imports
```
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add src/webpage_translation/driver/actions.py src/webpage_translation/driver/results.py src/webpage_translation/driver/fare_option.py
git commit -m "feat(driver): shared actions + pick first flight/fare"
```

---

## Task 13: `driver.booking_form` — reach guest form + detect login wall

**Files:**
- Create: `src/webpage_translation/driver/booking_form.py`

**Interfaces:**
- Produces:
  - `def reach_guest_form(browser: Browser, ctx: FlowContext) -> PageResult` — name `booking_form`.
  - Fill contact stub: email `test+qa@example.com`, phone `+6591234567`. Advance to passenger form via a Continue/Next button (AX by name).
  - Detect login wall via selector list `input[type=password], [data-testid=login-form], [aria-label*="Sign in" i]`. If found before form reachable → `error="auth_wall_hit"`, no submission.
  - Always screenshot whatever page is currently rendered (`booking_form.png`), scrape texts from that page.

- [ ] **Step 1: Implement**

Create `src/webpage_translation/driver/booking_form.py`:
```python
from __future__ import annotations

from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import PageResult


def _detect_auth_wall(browser: Browser) -> bool:
    selectors = [
        "input[type=password]",
        "[data-testid=login-form]",
        "[aria-label*='Sign in' i]",
    ]
    for sel in selectors:
        found = browser.eval_json(f"js('!!document.querySelector({sel!r})')")
        if found:
            return True
    return False


def _fill_input_by_placeholder(browser: Browser, needle: str, value: str) -> None:
    script = (
        f"js('for (const el of document.querySelectorAll(\"input\")) {{ if (el.placeholder && el.placeholder.toLowerCase().indexOf({needle.lower()!r}) >= 0) {{ el.focus(); break; }} }}')\n"
        f"type_text({value!r})\n"
    )
    browser.run(script)


def _click_ax_name(browser: Browser, needle: str) -> None:
    script = (
        "nodes = cdp('Accessibility.getFullAXTree')['nodes']\n"
        f"target = next(n for n in nodes if 'backendDOMNodeId' in n and n.get('name', {{}}).get('value', '').find({needle!r}) >= 0)\n"
        "box = cdp('DOM.getBoxModel', backendNodeId=target['backendDOMNodeId'])['model']['content']\n"
        "click_at_xy(sum(box[0::2]) / 4, sum(box[1::2]) / 4)\n"
    )
    browser.run(script)


def reach_guest_form(browser: Browser, ctx: FlowContext) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / "booking_form.png"
    url = "https://www.traveloka.com/flight/booking"
    error: str | None = None
    texts: tuple = ()
    try:
        if _detect_auth_wall(browser):
            error = "auth_wall_hit"
        else:
            _fill_input_by_placeholder(browser, "email", "test+qa@example.com")
            _fill_input_by_placeholder(browser, "phone", "+6591234567")
            _click_ax_name(browser, "Continue")
            browser.wait_for_load()
            if _detect_auth_wall(browser):
                error = "auth_wall_hit"
        browser.screenshot(shot)
        texts = extract_visible_texts(browser)
    except Exception as exc:
        error = f"booking_form failed: {exc}"
    return PageResult(
        name="booking_form",
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )
```

- [ ] **Step 2: Type-check + ruff**

Run:
```bash
uv run ruff check src/webpage_translation/driver/booking_form.py
uv run mypy src/webpage_translation/driver/booking_form.py --ignore-missing-imports
```
Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add src/webpage_translation/driver/booking_form.py
git commit -m "feat(driver): reach guest booking form + detect login wall"
```

---

## Task 14: `main.cli` — orchestrator + exit codes

**Files:**
- Modify: `src/webpage_translation/main.py`
- Create: `tests/unit/test_main_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `def cli(argv: Sequence[str] | None = None) -> int` — argparse: `--locale` (required), `--date` (YYYY-MM-DD, required), `--verbose` flag, `--report-root` (default `./report`).
  - Steps: build `FlowContext`, instantiate `Browser`. Try import chain: homepage → flight_search → results → fare_option → booking_form. After each: run `check_page`. Any `PageResult.error` sets `flow_broken=True` but processing continues to render the report. Compute exit code per §Global Constraints. Print summary line to stdout.
  - `def main() -> None: raise SystemExit(cli())` and update entry point to call `main`.
  - Update `pyproject.toml` entry point to `webpage-translation = "webpage_translation.main:main"`.

- [ ] **Step 1: Update `pyproject.toml` entry point**

Change the `[project.scripts]` line to:
```toml
[project.scripts]
webpage-translation = "webpage_translation.main:main"
```

Reinstall: `uv sync --extra dev`.

- [ ] **Step 2: Write failing test**

Create `tests/unit/test_main_cli.py`:
```python
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from webpage_translation.main import cli
from webpage_translation.qa.types import PageResult


def _mk(name: str, error: str | None = None) -> PageResult:
    return PageResult(
        name=name, url="u", timestamp="t", texts=(), screenshot=None, error=error
    )


@pytest.fixture
def stub_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_search,
        homepage,
        results,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage"))
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: _mk("flight_search"))
    monkeypatch.setattr(results, "pick_first", lambda b, c: _mk("results"))
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: _mk("booking_form"))
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", lambda: object())  # noqa: E731


def test_cli_returns_0_when_no_findings(stub_driver: None, tmp_path: Path):
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 0


def test_cli_returns_3_and_stops_when_homepage_broken(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from webpage_translation.driver import (
        booking_form,
        fare_option,
        flight_search,
        homepage,
        results,
    )
    monkeypatch.setattr(homepage, "open_and_set_locale", lambda b, c: _mk("homepage", error="boom"))
    called: list[str] = []
    monkeypatch.setattr(flight_search, "search", lambda b, c, **kw: called.append("fs") or _mk("flight_search"))
    monkeypatch.setattr(results, "pick_first", lambda b, c: called.append("r") or _mk("results"))
    monkeypatch.setattr(fare_option, "pick_first_fare", lambda b, c: called.append("fo") or _mk("fare_option"))
    monkeypatch.setattr(booking_form, "reach_guest_form", lambda b, c: called.append("bf") or _mk("booking_form"))
    from webpage_translation import main as m
    monkeypatch.setattr(m, "Browser", lambda: object())  # noqa: E731
    rc = cli(["--locale", "th-TH", "--date", "2026-08-31", "--report-root", str(tmp_path)])
    assert rc == 3
    assert called == []  # downstream steps never invoked
```

- [ ] **Step 3: Run — verify fail**

Run: `uv run pytest tests/unit/test_main_cli.py -v`
Expected: import failures / attribute errors.

- [ ] **Step 4: Implement `main.py`**

Rewrite `src/webpage_translation/main.py`:
```python
from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from webpage_translation.context import FlowContext
from webpage_translation.driver import booking_form, fare_option, flight_search, homepage, results
from webpage_translation.driver.browser import Browser, BrowserError
from webpage_translation.qa.checker import check_page
from webpage_translation.qa.types import Finding, PageResult
from webpage_translation.report.data import build_payload, write_json
from webpage_translation.report.render import render_report


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="webpage-translation")
    p.add_argument("--locale", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--report-root", default="./report")
    return p.parse_args(argv)


def _run_flow(
    browser: Browser, ctx: FlowContext
) -> list[tuple[PageResult, tuple[Finding, ...]]]:
    steps: list[PageResult] = []
    home = homepage.open_and_set_locale(browser, ctx)
    steps.append(home)
    if home.error is None:
        steps.append(flight_search.search(browser, ctx))
        steps.append(results.pick_first(browser, ctx))
        steps.append(fare_option.pick_first_fare(browser, ctx))
        steps.append(booking_form.reach_guest_form(browser, ctx))
    return [(page, check_page(page, ctx.locale)) for page in steps]


def cli(argv: Sequence[str] | None = None) -> int:
    args = _parse(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    report_dir = Path(args.report_root) / stamp
    ctx = FlowContext(
        locale=args.locale,
        date=args.date,
        screenshots_dir=report_dir / "_captures",
    )
    try:
        browser = Browser()
    except BrowserError as exc:
        logging.error("browser init failed: %s", exc)
        print("hint: run `browser-use --doctor`")
        return 2
    try:
        results_out = _run_flow(browser, ctx)
    except BrowserError as exc:
        logging.error("browser error: %s", exc)
        return 2
    payload = build_payload(results_out, locale=args.locale, date=args.date)
    render_report(report_dir, payload)
    write_json(report_dir / "data.json", payload)
    findings_total = sum(len(f) for _, f in results_out)
    flow_broken = any(p.error is not None for p, _ in results_out)
    print(
        f"{len(results_out)} pages, {findings_total} findings — see {report_dir / 'index.html'}"
    )
    if flow_broken:
        return 3
    return 1 if findings_total > 0 else 0


def main() -> None:
    raise SystemExit(cli())
```

- [ ] **Step 5: Run test — verify pass**

Run: `uv run pytest tests/unit/test_main_cli.py -v`
Expected: PASS.

- [ ] **Step 6: Full unit suite + coverage gate**

Run:
```bash
uv run pytest tests/unit --cov=src/webpage_translation/qa --cov=src/webpage_translation/report --cov-fail-under=80
uv run ruff check src/webpage_translation
uv run mypy src/webpage_translation/qa src/webpage_translation/report
```
Expected: PASS across the board.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/webpage_translation/main.py tests/unit/test_main_cli.py
git commit -m "feat(main): CLI orchestrator with exit codes + report render"
```

---

## Task 15: E2E smoke + README

**Files:**
- Create: `tests/e2e/test_full_flow_th.py`
- Create: `README.md`

**Interfaces:**
- Consumes: full CLI.
- Produces:
  - `README.md` with quickstart: prereqs (Chrome remote-debug per browser-use SKILL), `uv sync`, run command, exit codes table, coverage command.
  - E2E test that runs the CLI end-to-end with `RUN_E2E=1` gate, asserts report file exists and ≥ 5 `pages` in `data.json`.

- [ ] **Step 1: Write e2e test**

Create `tests/e2e/test_full_flow_th.py`:
```python
import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "1", reason="set RUN_E2E=1 to enable"
)


def test_full_flow_th(tmp_path: Path):
    target = (date.today() + timedelta(days=45)).isoformat()
    result = subprocess.run(
        [
            "uv", "run", "webpage-translation",
            "--locale", "th-TH",
            "--date", target,
            "--report-root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1, 3), result.stderr
    reports = sorted(tmp_path.iterdir())
    assert reports, "no report dir created"
    index = reports[-1] / "index.html"
    data = json.loads((reports[-1] / "data.json").read_text(encoding="utf-8"))
    assert index.exists()
    assert 1 <= len(data["pages"]) <= 5  # 1 when homepage failed (stop-on-fail), else 5
```

- [ ] **Step 2: Write README**

Create `README.md`:
```markdown
# webpage-translation

Locale QA for `traveloka.com` booking flow. Scrapes the 5-step flow under a
chosen non-English locale and flags text whose detected language does not
match the locale.

## Prereqs

- macOS with Chrome or Chromium installed
- Enable Chrome remote debugging via the `browser-use` skill; if the daemon
  fails to connect, run `browser-use --doctor` and follow prompts
- `uv` (`brew install uv`)

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run webpage-translation --locale th-TH --date 2026-08-31
```

Report is written to `./report/<timestamp>/index.html` alongside `data.json`
and a `screenshots/` directory.

## Supported locales

`en-SG`, `id-ID`, `th-TH`, `vi-VN`, `zh-CN`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Clean run, no findings |
| 1 | Clean run, findings > 0 |
| 2 | Infrastructure error (Chrome, deps) |
| 3 | Flow broke mid-run |

## Tests

```bash
uv run pytest tests/unit                    # fast, no browser
RUN_BROWSER_TESTS=1 uv run pytest tests/integration
RUN_E2E=1 uv run pytest tests/e2e
```

Unit coverage floor: 80% on `qa/` and `report/`. Lint: `uv run ruff check`.
Types: `uv run mypy src/webpage_translation/qa src/webpage_translation/report`.
```

- [ ] **Step 3: Verify e2e is skip-gated**

Run: `uv run pytest tests/e2e -v`
Expected: 1 skipped.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e README.md
git commit -m "docs+test: add README and gated e2e smoke test"
```

- [ ] **Step 5: Final full-suite verification**

Run:
```bash
uv run ruff check
uv run mypy src/webpage_translation/qa src/webpage_translation/report
uv run pytest tests/unit --cov=src/webpage_translation/qa --cov=src/webpage_translation/report --cov-fail-under=80
```
Expected: all green.

---

## Self-Review

**Spec coverage:**
- Homepage locale switch → Task 10.
- Flight search SIN→SHA one-way on date → Task 11.
- Results list, pick first → Task 12.
- Fare option, pick first → Task 12.
- Booking form guest path + auth-wall detect → Task 13.
- Visible-text extraction via DOM walk → Task 9.
- Language detection via lingua → Task 4.
- Allowlist (brands/codes/prices) → Task 3.
- Findings → Task 5.
- HTML report + screenshots + overlays → Task 7.
- JSON side-file → Task 6.
- Exit codes 0/1/2/3 → Task 14.
- 80% coverage on `qa/` + `report/` → Task 14 Step 6, Task 15 Step 5.
- Types (`PageResult`, `TextItem`, `Finding`, `BBox`) → Task 2.
- Logging + verbose flag → Task 14.
- Report dir timestamped, never overwrite → Task 7, Task 14.
- Auth-wall halts flow without prompting → Task 13.

**Placeholder scan:** no TBD/TODO/handwaving. All test code and impl code inlined.

**Type consistency:** `PageResult`, `TextItem`, `Finding`, `BBox` defined in Task 2 and used consistently downstream. `FlowContext` defined in Task 8, used by Tasks 10–13 and Task 14. `Browser` API surface (`run`, `eval_json`, `new_tab`, `wait_for_load`, `screenshot`) defined in Task 8 and used only by later tasks. `check_page` signature in Task 5 matches call in Task 14.

No issues found.
