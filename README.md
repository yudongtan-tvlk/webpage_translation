# webpage-translation

Locale QA for `traveloka.com`. Drives Traveloka's 4-step flight-booking flow
under a chosen locale, extracts every visible text on each page, and flags
strings whose detected language is English on a non-English locale —
surfacing missing translations, untranslated buttons, and dangling i18n
keys.

## Prereqs

- macOS with Chrome or Chromium installed
- `browser-use` CLI on `PATH` (installed globally, e.g.
  `uv tool install browser-use`)
- Enable Chrome remote debugging via the `browser-use` skill; if the daemon
  fails to connect, run `browser-use --doctor` and follow prompts
- `uv` (`brew install uv`)

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run webpage-translation --locale ja-JP --date 2026-09-05
```

Options:

- `--locale <bcp47>` (required) — see Supported locales below.
- `--date YYYY-MM-DD` (required) — outbound departure date used to build
  the flight-search deep link.
- `--report-root <dir>` — where reports go. Defaults to `./reports`.
- `--verbose` — DEBUG-level logging.

Each run writes to `./reports/<locale>-<timestamp>/index.html` alongside
`data.json` and a `screenshots/` directory. Reports never overwrite; every
invocation gets a fresh directory.

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
│   └── checker.py       per-page finding generator
└── report/              Jinja2 HTML + JSON dumper
    ├── data.py          build_payload + write_json
    ├── render.py        Jinja2 HTML report generator
    └── templates/       index.html.j2, page.html.j2
```

Layer rule: `driver` may import `qa.types` only; `qa` never imports
`driver`; `report` may import `qa` types.
