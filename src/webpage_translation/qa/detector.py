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
