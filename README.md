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
