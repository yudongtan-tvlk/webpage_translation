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
