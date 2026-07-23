# webpage-translation

Locale QA for `traveloka.com`. Drives Traveloka's 4-step flight-booking flow
under a chosen locale, extracts every visible text on each page, and flags
strings whose detected language is English on a non-English locale —
surfacing missing translations, untranslated buttons, and dangling i18n
keys.

## Prereqs

- macOS with Chrome or Chromium installed.
- `uv` (`brew install uv`).
- `browser-use` CLI on `PATH`: `uv tool install browser-use` then
  `browser-use skill install`.
- Optional (for `--gemini-review`): create
  `src/webpage_translation/.env` containing
  `GEMINI_KEY="<your key>"`. The file is gitignored — it never leaves
  your machine. Paid billing on the Gemini project recommended (the
  free tier caps at 20 requests/day per model).

## Install

```bash
cd webpage_translation
uv sync --extra dev
```

## Running the tool

### 1. Attach Chrome (first run only)

On the first invocation each session, `browser-use` opens
`chrome://inspect/#remote-debugging` and prompts you to tick
**"Allow remote debugging for this browser instance"** — click Allow.

Quick verify:

```bash
browser-use <<'PY'
print(page_info())
PY
```

If it hangs or errors with `CDP WS handshake failed`:

```bash
pkill -f browser-harness            # kill any stale daemon
browser-use --doctor                # diagnostics
# then re-tick Allow in Chrome and rerun the command
```

### 2. Run one locale

```bash
uv run webpage-translation --locale th-TH --date 2026-09-05
```

Prints a summary line and writes a fresh directory
`./reports/<locale>-<YYYYMMDD-HHMMSS>/` containing `index.html`,
`data.json`, and `screenshots/*.png`. Open the HTML in a browser:

```bash
open "$(ls -td reports/*/ | head -1)/index.html"
```

### 3. Run with Gemini native-quality review

Adds a per-page LLM review (score, issue list, recommended fixes,
format-convention checks) alongside the regex checker. Requires the
key from Prereqs.

```bash
uv run webpage-translation --locale ja-JP --date 2026-09-05 --gemini-review
```

### 4. Loop over locales

```bash
DATE=$(python3 -c 'from datetime import date, timedelta; print((date.today()+timedelta(days=45)).isoformat())')
for LOC in th-TH vi-VN ja-JP ko-KR zh-EN; do
  uv run webpage-translation --locale "$LOC" --date "$DATE" --gemini-review
done
open "$(ls -td reports/*/ | head -1)/index.html"
```

### All flags

| Flag | Required | Description |
|---|---|---|
| `--locale <BCP47>` | yes | see Supported locales below |
| `--date YYYY-MM-DD` | yes | outbound flight date (used in deep link) |
| `--report-root <dir>` | no (default `./reports`) | output directory |
| `--gemini-review` | no | also send screenshots to Gemini |
| `--verbose` | no | DEBUG-level logging |

Each run writes to `./reports/<locale>-<timestamp>/index.html` alongside
`data.json` and a `screenshots/` directory. Reports never overwrite;
every invocation gets a fresh directory.

## What it flags

- **Non-English locale** (any of `id-ID`, `th-TH`, `vi-VN`, `zh-CN`,
  `zh-EN`, `ja-JP`, `ko-KR`, `ms-MY`): emits a Finding for each text whose
  detected language is English and that is not in the built-in allowlist
  (brand names, IATA/airline codes, currency-prefixed prices, pure
  numbers).
- **English locale** (`en-SG`): emits nothing — self-check is meaningless.

Detection uses `lingua-language-detector` with a confidence floor of
`MIN_CONFIDENCE = 0.5`; anything below is treated as `unknown` and
skipped.

## Gemini native-quality review (opt-in)

With `--gemini-review`, every screenshot is downscaled (max 2000px long
edge) and sent to Gemini Flash along with a locale-aware prompt asking
for:

1. English contamination — any user-facing English strings a native
   speaker would flag.
2. Native quality of the target-locale prose — score 1..5, one-sentence
   summary, and a table of enumerated issues (`quality_detail`) with
   detail + recommended fix per issue.
3. Format-convention mismatches — currency placement, number
   separators, date/time order, measurement units.

Primary model: `gemini-3.6-flash`. Automatically falls back to
`gemini-flash-latest` on 429 (both share the same project-wide daily
quota on the free tier; billing recommended).

## Supported locales

`en-SG`, `id-ID`, `th-TH`, `vi-VN`, `zh-CN`, `zh-EN`, `ja-JP`, `ko-KR`,
`ms-MY`.

Each maps to Traveloka's regional URL (`/<lang>-<region>/`). The driver
navigates directly to the regional homepage and flight-search deep-link;
the locale/currency chip on the top nav is never clicked.

## Flow captured per run

1. `homepage` — `https://www.traveloka.com/<locale>/`
2. `flight_search` — deep-linked
   `/<locale>/flight/fullsearch?ap=SIN.SHA&dt=DD-MM-YYYY.NA&ps=1.0.0&sc=ECONOMY`
3. `fare_option` — opens the bundle overlay for the first flight via
   `data-testid=flight-inventory-card-button`, scrapes the fare tray
4. `booking_form` — guest-path booking form (reached by clicking
   `button_ticket_option_select_0`), no submission

If the homepage fails to load, downstream steps are skipped and the CLI
exits `3`.

## Screenshots

Full-page PNGs. `browser.screenshot` queries
`document.documentElement.scrollHeight` at capture time (and honours a
`min_height` derived from the extracted bboxes) so virtualized flight
lists don't get truncated. Overlays in the HTML report are scaled at
`load`/`resize` to match the displayed image ratio via inline JS.

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

Unit coverage floor: 80% on `qa/` and `report/`. Currently ~98%.
Lint: `uv run ruff check`.
Types: `uv run mypy src/webpage_translation/qa src/webpage_translation/report`.

## Layout

```
src/webpage_translation/
├── main.py              CLI + orchestrator
├── context.py           FlowContext dataclass
├── driver/              browser-use subprocess wrapper + per-page drivers
│   ├── browser.py       subprocess wrapper (never `import browser_use`)
│   ├── actions.py       wait_for_selector, wait_until_stable, click_first
│   ├── extract.py       visible-text DOM walker (document-space bboxes)
│   ├── homepage.py      /<locale>/ landing page
│   ├── flight_search.py deep-link flight fullsearch
│   ├── fare_option.py   opens bundle tray + scrapes fare panel
│   └── booking_form.py  guest booking form
├── qa/                  pure language QA (no browser deps)
│   ├── types.py         frozen dataclasses (BBox, TextItem, PageResult, Finding)
│   ├── allowlist.py     brand + code + price regex/set filter
│   ├── detector.py      lingua wrapper (cached)
│   ├── checker.py       per-page finding generator
│   └── gemini_review.py Gemini Flash native-quality review (opt-in)
└── report/              Jinja2 HTML + JSON dumper
    ├── data.py          build_payload + write_json
    ├── render.py        Jinja2 HTML report generator
    └── templates/       index.html.j2, page.html.j2
```

Layer rule: `driver` may import `qa.types` only; `qa` never imports
`driver`; `report` may import `qa` types.
