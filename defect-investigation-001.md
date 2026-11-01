# Defect Investigation 001 — Windows SQLite test cleanup

**Project:** Bug Investigation Tracker  
**Component:** Automated test teardown (not the application's bug-tracking workflow)  
**Environment:** Windows, Python 3.13 ARM64, SQLite  
**Status:** Fixed and verified locally  
**Evidence:** Local terminal results, November 1, 2026

## Summary

While running the project's 10-test `unittest` suite on Windows, `test_missing_bug_does_not_create_orphan_notes` encountered an error during cleanup of the temporary test database:

```text
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '...\test.db'
```

The initial run reported **10 tests, 1 error**. This was a **test resource-cleanup issue**, not a demonstrated defect in persistent bug records or a deployed application.

## Investigation and root cause

The test used `with sqlite3.connect(self.db) as conn:`. SQLite's connection context manager commits or rolls back transactions but does **not** close the connection when the block exits. On Windows, the open connection prevented `TemporaryDirectory.cleanup()` from deleting the database file.

## Correction

The test was updated to explicitly close its connection using `contextlib.closing`:

```python
from contextlib import closing

with closing(sqlite3.connect(self.db)) as conn:
    # Existing assertions
    ...
```

Only the test cleanup was corrected. The application logic and database schema were not modified for this fix.

## Verification

After the correction, the test suite was rerun:

```powershell
py -3 -m unittest discover -s tests -v
```

**Observed result:** `Ran 10 tests in 0.116s` followed by `OK`, including a passing result for `test_missing_bug_does_not_create_orphan_notes`.

Separately, manual CLI verification confirmed that a synthetic bug record could be created, retrieved, annotated, moved to `investigating`, and filtered by status.

## Engineering lessons

- Reproduce and isolate platform-specific test failures.
- Distinguish test infrastructure issues from application defects.
- Understand SQLite connection lifetimes and Windows file locks.
- Apply a targeted fix and rerun the original verification suite.

**Scope:** This evidence supports a successful local Windows test run. It does not establish hosted CI, production deployment, or exhaustive cross-platform testing. The demo login-form issue is synthetic data, not a separately verified real-world defect.
