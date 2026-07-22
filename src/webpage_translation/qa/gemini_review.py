"""Gemini-backed native-quality review of a page screenshot.

Given a `PageResult` with a screenshot, ask Gemini Flash to judge:
  1. Are there English texts on the page?
  2. Is the target-locale prose native and natural?
  3. Are numeric formats (currency, date, unit, metric) consistent with
     the target locale's convention?

The screenshot is downscaled to a max long edge before upload to keep
request size small.
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-flash-latest"
MAX_LONG_EDGE = 2000

_LOCALE_NAMES: dict[str, str] = {
    "th-TH": "Thai (Thailand)",
    "id-ID": "Bahasa Indonesia (Indonesia)",
    "vi-VN": "Vietnamese (Vietnam)",
    "zh-CN": "Simplified Chinese (China)",
    "zh-EN": "Simplified Chinese (Traveloka's Chinese-region site)",
    "ja-JP": "Japanese (Japan)",
    "ko-KR": "Korean (South Korea)",
    "ms-MY": "Malay (Malaysia)",
    "en-SG": "English (Singapore)",
}


@dataclass(frozen=True, slots=True)
class GeminiReview:
    page: str
    model: str
    english_present: bool
    english_examples: tuple[str, ...]
    quality_score: int  # 1-5
    quality_summary: str
    format_issues: tuple[str, ...]
    raw: str  # full JSON text from the model, for the report

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "model": self.model,
            "english_present": self.english_present,
            "english_examples": list(self.english_examples),
            "quality_score": self.quality_score,
            "quality_summary": self.quality_summary,
            "format_issues": list(self.format_issues),
            "raw": self.raw,
        }


def load_api_key(env_path: Path | None = None) -> str | None:
    key = os.environ.get("GEMINI_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() in {"GEMINI_KEY", "GEMINI_API_KEY"}:
            return value.strip().strip('"').strip("'")
    return None


def _downscale_png(path: Path, max_long_edge: int = MAX_LONG_EDGE) -> bytes:
    img: Image.Image = Image.open(path)
    w, h = img.size
    long_edge = max(w, h)
    if long_edge > max_long_edge:
        scale = max_long_edge / long_edge
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _build_prompt(locale: str) -> str:
    locale_name = _LOCALE_NAMES.get(locale, locale)
    return f"""You are a localization QA reviewer. The screenshot below is one page of a travel-booking website whose target locale is **{locale_name}** (BCP-47: `{locale}`).

Judge the page on THREE things:

1. **English contamination.** Are there user-facing English texts that should have been translated? Ignore product/brand names (Traveloka, Visa, airline names, IATA codes like SIN/SHA), currency codes, and email/URL fragments.
2. **Native quality of the target-locale prose.** Is the language natural and idiomatic to a first-language speaker of {locale_name}? Or does it read like machine translation or awkward, literal English mapping?
3. **Format conventions.** Currency symbol placement, number thousands/decimal separators, date order, time format (12h vs 24h), measurement units, metric-vs-imperial — do they match what a native {locale_name} user expects?

Reply with **exactly one JSON object** and nothing else, following this schema:
```
{{
  "english_present": <boolean>,
  "english_examples": [<up to 8 verbatim English strings you saw, or []>],
  "quality_score": <integer 1..5, where 5=native and idiomatic, 1=broken>,
  "quality_summary": "<one or two sentences on the target-locale prose quality>",
  "format_issues": [<0..8 short strings, each describing one convention mismatch e.g. 'dates rendered as MM/DD/YYYY instead of DD/MM/YYYY'>]
}}
```
No markdown, no code fences in your response — just the JSON."""


def _parse_reply(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        # Strip a ``` or ```json fence if the model added one anyway.
        parts = stripped.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("{"):
                stripped = candidate
                break
    result: dict[str, Any] = json.loads(stripped)
    return result


def review_page(
    *,
    page_name: str,
    screenshot: Path,
    locale: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    max_long_edge: int = MAX_LONG_EDGE,
) -> GeminiReview:
    import time

    client = genai.Client(api_key=api_key)
    png_bytes = _downscale_png(screenshot, max_long_edge=max_long_edge)
    prompt = _build_prompt(locale)
    image_part = types.Part.from_bytes(data=png_bytes, mime_type="image/png")
    contents: list[Any] = [image_part, prompt]
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model, contents=contents)
            break
        except Exception as exc:  # includes transient 503s
            last_exc = exc
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    else:  # pragma: no cover — for loop always returns via break or raise
        raise RuntimeError(f"unreachable: {last_exc}")
    raw = (response.text or "").strip()
    parsed = _parse_reply(raw)
    return GeminiReview(
        page=page_name,
        model=model,
        english_present=bool(parsed.get("english_present", False)),
        english_examples=tuple(str(x) for x in (parsed.get("english_examples") or [])),
        quality_score=int(parsed.get("quality_score", 0)),
        quality_summary=str(parsed.get("quality_summary", "")).strip(),
        format_issues=tuple(str(x) for x in (parsed.get("format_issues") or [])),
        raw=raw,
    )
