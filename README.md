# Bug Investigation Tracker

A focused **Python + SQLite** command-line application for recording software defects and investigation notes. Designed as a small, independently understandable engineering portfolio exercise, with synthetic examples only.

## What it demonstrates

- SQLite schema constraints, primary and foreign keys, and persistent storage
- Parameterized SQL queries and transaction rollback on errors
- Input validation, status filtering, and investigation-note history
- Standard-library automated tests, including invalid inputs and SQL-injection payload handling
- No third-party dependencies and no accounts or credentials

## Quick start

Requires Python 3.10+.

```bash
python tracker.py add "Login button does not respond" --severity high --description "Reproduced on synthetic local demo"
python tracker.py list
python tracker.py status 1 investigating
python tracker.py note 1 "Investigating reproduction steps"
python tracker.py show 1
python -m unittest discover -s tests -v
```

On Windows, use `py -3` instead of `python` if necessary. Data goes into `bugs.db` in your current working directory. Specify `--db path/to/file.db` before the command to choose another database location.

## Design decisions

- Only four statuses are supported: `open`, `investigating`, `resolved`, and `closed`. No workflow transition policy is imposed.
- Severity is `low`, `medium`, `high`, or `critical`.
- A note has an immutable creation timestamp. Bugs store UTC creation and last-updated timestamps.
- All database writes use parameters; SQLite CHECK/foreign-key constraints provide additional safeguards.
- This is **not** a production-ready, multi-user ticketing system. It has no login, API, web UI, or network access.

## Verification

Run `python -m unittest discover -s tests -v`. Tests use a fresh temporary database and don't touch your regular `bugs.db`. This README does not claim a hosted CI run. See actual local test output for the current execution result.

### Defect investigation

[Windows SQLite Test Cleanup — Root Cause and Resolution](defect-investigation-001.md)

## Privacy

Only use synthetic bug data in a public repository. Local `.db` files are excluded from Git. Do not paste proprietary customer, business, or security findings into public samples.

## Project structure

```text
tracker.py             CLI, validation, SQLite operations
tests/test_tracker.py  Regression tests
.gitignore             Ignore local data and Python caches
README.md              Usage and design
```
