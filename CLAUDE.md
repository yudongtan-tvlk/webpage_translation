# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Greenfield. Only `prd.txt` and `.claude/settings.local.json` exist — no source, tests, build system, or dependencies committed yet. Architecture and commands below reflect the product intent in `prd.txt`; expand this file as real code lands.

## Product Intent (from `prd.txt`)

Scrape webpages of a target website and verify that on-page text matches the selected locale (currency/language).

Concrete flow required by the PRD:
1. Open `traveloka.com` homepage and switch to a non-English locale (currency).
2. Drive a booking journey via **browser-use**: flight search → one-way SIN → SHA on August 31 → first flight in results → first fare option → booking form page.
3. On every visited page, scrape all displayed text, compare each text's detected language against the active locale, and log/alert any mismatched strings.

Two distinct concerns to keep separated in code:
- **Navigation/scrape driver** — deterministic, page-aware steps against Traveloka's UI (locale switch, search form, results list, fare option, booking form).
- **Locale QA** — pure functions that take `(text, expected_locale)` and produce mismatch findings. Should be reusable across pages and testable without a browser.

## Tooling

- **Browser automation:** `browser-use` (CDP-attached to local Chrome via `browser-use skill install`). See `~/.claude/skills/browser-use/SKILL.md`. First navigation uses `new_tab(url)`, not `goto_url`. Prefer AX tree + `click_at_xy` over screenshot-driven clicks. Call `wait_for_load()` after navigation.
- **Language detection:** not yet chosen. When picking one, favor libraries that handle short strings and CJK/Thai/Indonesian (Traveloka's likely locales) — `lingua`, `fasttext-langdetect`, or `langid` are reasonable candidates. Record the choice here once made.

## Commands

None committed. Add build/lint/test commands to this file the moment the first `pyproject.toml`/`package.json` lands, including how to run a single test.

## Notes for Future Sessions

- The PRD hardcodes the SIN→SHA August 31 journey; treat the date as a moving target and parameterize it rather than hardcoding when implementing.
- Locale switching on Traveloka changes both currency and UI language — do not assume language follows currency 1:1; scrape the actual `<html lang>` / rendered strings to determine the "expected" locale for QA.
- Booking form is a login-walled path on some flows. Per browser-use skill guidance: stop and ask on password/MFA/consent prompts.
