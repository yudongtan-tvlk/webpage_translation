# Traveloka Locale QA — Design

**Date:** 2026-07-21
**Source:** `prd.txt`
**Status:** Approved (brainstorming phase)

## Problem

Scrape a fixed 5-step booking flow on `traveloka.com` under a chosen non-English locale, then flag any on-page text whose detected language does not match the locale. Deliver a per-run HTML report with screenshots and highlighted mismatches.

## Scope

**In scope**
- Fixed PRD flow: homepage → locale switch → flight search (SIN → SHA, one-way) → results list → first flight → first fare option → booking form (guest path).
- Parameterized target locale (default candidate: `th-TH`) and departure date.
- Visible-text extraction via DOM walk in JS.
- Language detection with `lingua`.
- Allowlist filter (brand names, IATA/airline codes, digits, currency-prefixed prices).
- HTML report with screenshots + finding tables + JSON side-file.

**Out of scope**
- Non-Traveloka sites.
- Localizations other than the ones lingua supports.
- OCR fallback.
- Actual booking submission.
- Retrying flow across dates when a date is sold out.
- Login/MFA/consent handling (halt as an error and skip to next page).

## Success Criteria

1. `webpage-translation --locale th-TH --date 2026-08-31` completes end-to-end without human intervention (barring Chrome remote-debug enablement).
2. Report file `./report/<timestamp>/index.html` opens in a browser and lists ≥ 5 pages with screenshots, findings tables, and per-finding highlight overlays.
3. Machine-readable `data.json` alongside HTML contains identical findings.
4. Exit codes match the table under §Error Handling.
5. `qa/` and `report/` modules hit ≥ 80% unit-test coverage without a live browser.

## Architecture

Single Python package `webpage_translation` (Python 3.12, uv-managed). Entry point CLI `webpage-translation`.

Three layers, no upward imports:

1. **`driver/`** — browser automation via `browser-use` helpers. One module per PRD page. Each exposes a function that returns a `PageResult`.
2. **`qa/`** — pure functions. Detector wrapper, allowlist rules, per-page checker. No browser deps.
3. **`report/`** — Jinja2 HTML renderer + JSON dumper.

Orchestrator (`main.py`) parses args, loops through the fixed page sequence, collects `PageResult`s, runs QA, renders report. 30–50 lines.

### Data types

```
FlowContext   = {tab_id, locale, date, currency, current_url}
TextItem      = {text: str, selector: str, bbox: {x, y, w, h}}
PageResult    = {name: str, url: str, timestamp: str,
                 texts: list[TextItem], screenshot: Path,
                 error: str | None}
Finding       = {page: str, text: str, selector: str,
                 detected: str, expected: str, confidence: float}
```

## Components

### `driver/`

- `homepage.py::open_and_set_locale(locale) -> PageResult`
  Opens `https://www.traveloka.com` via `new_tab`, clicks locale/currency widget, selects target locale, waits for load, scrapes.
- `flight_search.py::search(ctx, origin='SIN', dest='SHA', date, one_way=True) -> PageResult`
  Ensures Flights tab active. Fills origin/dest via autocomplete (click AX suggestion). Picks date on calendar (bounded month-forward clicks). Clicks Search.
- `results.py::pick_first(ctx) -> PageResult`
  Waits for result cards, scrapes, clicks first card.
- `fare_option.py::pick_first_fare(ctx) -> PageResult`
  Waits for fare list, scrapes, clicks first fare.
- `booking_form.py::reach_guest_form(ctx) -> PageResult`
  Fills guest contact stub (dummy email/phone), advances to passenger form, scrapes. Never submits. Detects and records login walls without prompting.

Shared JS primitive `extract_visible_texts()` injected via `js(...)`:
- Walks DOM.
- Keeps nodes with non-empty trimmed `textContent`, non-zero bounding rect, and computed style visibility != hidden.
- Returns `[{text, selector, bbox}]`.

### `qa/`

- `detector.py` — wraps `lingua.LanguageDetectorBuilder`. Preloads the union of supported locales at module import. Returns ISO code and confidence.
- `allowlist.py` — regex + literal set:
  - `^[A-Z]{2,3}$` (IATA / country codes)
  - `^[A-Z0-9]{2}\s?\d+$` (airline flight codes)
  - `^\d+([.,\d]*)?$` (pure numbers)
  - Currency-prefixed prices (`^[¥$€£฿₫Rp]\s?[\d.,]+$` and locale variants)
  - Literal brand set loaded from `qa/data/brands.json` (`Traveloka`, `Visa`, `Mastercard`, `AMEX`, common airline names).
- `checker.py::check_page(page: PageResult, expected: str) -> list[Finding]`
  Skips allowlisted texts. Runs detector. Emits Finding for mismatches. Emits Finding with `detected='unknown'` when confidence below threshold (constant, default 0.5).

### `report/`

- `render.py` — Jinja2 template. Per page block: screenshot with absolutely-positioned `<div>` overlays keyed on `TextItem.bbox`; table of findings; error banner if `PageResult.error`.
- `data.py` — dumps raw `PageResult` and `Finding` lists to `data.json` alongside HTML.

## Data Flow

```
CLI args (locale, date)
   │
   ▼
main.py
   │  for each PRD step in fixed order:
   ▼
driver.<step>(ctx) ──► PageResult (texts + screenshot)
   │
   ▼
qa.checker.check_page(PageResult, locale) ──► list[Finding]
   │
   ▼
accumulate: list[(PageResult, Findings)]
   │  (all pages done or flow broke)
   ▼
report.render(results) ──► ./report/<timestamp>/index.html + screenshots/ + data.json
   │
   ▼
stdout: "N pages, M findings — see ./report/<timestamp>/index.html"
```

Between-step state passed forward as a small `FlowContext` dict. No page-object statefulness. No globals.

Language detection batched per page — single loop over texts, one detector call per string (lingua is stateless per call).

## Error Handling

| Failure | Where | Response |
|---|---|---|
| Chrome CDP not reachable | driver startup | Print `browser-use --doctor` hint. Exit 2. |
| Locale switch selector broke | `homepage.py` | Retry once with 2s backoff. Second failure: record error PageResult, stop flow. Exit 3 after report. |
| Click misses (stale AX node) | any driver | Refetch AX tree, retry once. Second miss: record error, skip page. |
| Autocomplete never appears | `flight_search.py` | 10s wait, then error PageResult, skip forward. |
| Date picker cannot reach target | `flight_search.py` | Bounded month-forward clicks (max 24). Overshoot: error, skip. |
| Page load timeout | any driver | `wait_for_load(timeout=30)`. Timeout: error PageResult, continue. |
| Login wall hit unexpectedly | `booking_form.py` | Detect login selector. Record `auth_wall_hit` error PageResult. Skip. No prompt. |
| Detector returns `Unknown` | `qa/checker.py` | Not an error. Emit Finding with `detected='unknown'`. Rendered as neutral warning row. |
| Report dir collision | `report/render.py` | Timestamped subdir `YYYYMMDD-HHMMSS`. Never overwrite. |

Logging via stdlib `logging`. Default INFO. `--verbose` enables DEBUG. Driver actions logged with page + selector. Errors include stack traces. Only dummy passenger data ever hits logs.

Exit codes:
- `0` — clean run, findings = 0
- `1` — clean run, findings > 0
- `2` — infrastructure error (Chrome, deps)
- `3` — flow broke mid-run

## Testing

### Unit (`tests/unit/`, no browser)

- `test_detector.py` — canonical short strings per supported locale; assert detected ISO code and confidence bounds.
- `test_allowlist.py` — table of skipped vs non-skipped cases; edge cases like `SQ 851 to Shanghai` (mixed).
- `test_checker.py` — synthetic `PageResult` + expected locale → assert Finding list, including `unknown` path.
- `test_report_render.py` — synthetic results → render to temp dir → assert HTML contains screenshot refs + finding rows and `data.json` parses.

### Integration (`tests/integration/`, browser required, gated by env `RUN_BROWSER_TESTS=1`)

- `test_extract_visible_texts.py` — local HTML fixture with hidden / visible / aria-only elements → assert JS extractor returns only visible.
- `test_homepage_locale_switch.py` — live homepage, switch to `th-TH`, assert `<html lang>` or currency indicator matches expected. Skipped in CI.

### E2E smoke (`tests/e2e/`, manual)

- `test_full_flow_th.py` — end-to-end run against a future date. Asserts structural: report exists, ≥ 5 `PageResult`s written, exit code ≠ 2. No semantic content assertions.

### Fixtures

Snapshots of each PRD page saved via a helper script and checked into `tests/fixtures/`. Used to drive detector + extractor unit tests offline.

### Quality gates

- `pytest --cov=qa --cov=report --cov-fail-under=80`
- `ruff check`
- `mypy --strict qa/ report/`

## Open Questions

None at design approval time.

## Non-Decisions (Deferred)

- Page-object refactor — revisit if flow expands to multi-locale × multi-journey matrix.
- Cloud browser (`start_remote_daemon`) — revisit if captcha rate becomes a blocker on repeat runs.
- Report diffing across runs — revisit once baseline reports exist.
