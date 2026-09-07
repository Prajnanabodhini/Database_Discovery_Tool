# Prompt 02 — Baseline, Branch, Diff and Guardrails

## Objective

Create a reproducible implementation baseline before any v3.1.1 edits.

## Required checks

1. Confirm repository is `Prajnanabodhini/Database_Discovery_Tool`.
2. Confirm `main` currently points to `e2188237809efdcc324a79930640628a3975c8d6` unless the user has explicitly provided a newer approved base.
3. If HEAD differs:
   - stop implementation,
   - document the new SHA,
   - compare it against `e2188237809efdcc324a79930640628a3975c8d6`,
   - determine whether the independent findings are already changed.
4. Record:
   - `git status`
   - `git log --oneline --decorate -n 10`
   - package version
   - Python version
   - number of production Python files
   - number of tests
5. Run:
   - `python -m compileall -q main.py src`
   - `python -m pytest -q -p no:cacheprovider -m "not live" tests`
6. Do not create a DB connection.
7. Verify `output/` and `git_export/` were absent before and remain absent after offline baseline.
8. Inspect current GitHub Actions status if available.

## Branch

If the operator's workflow allows branch creation, use:

`v3.1.1-hardening`

Otherwise work on the explicitly approved branch only.

Never force-update or rewrite `main`.

## Required regression searches

Search production source for:

- `execute(`
- `executemany`
- `exec(`
- `eval(`
- `os.system`
- `subprocess`
- `shell=True`
- `OPENQUERY`
- `OPENROWSET`
- `OPENDATASOURCE`
- `xp_cmdshell`
- `sp_executesql`
- `INSERT`
- `UPDATE`
- `DELETE`
- `MERGE`
- `CREATE`
- `ALTER`
- `DROP`
- `TRUNCATE`
- `BACKUP`
- `RESTORE`
- eager `mkdir`
- `output`
- `git_export`

Classify each occurrence rather than blindly replacing text.

## Deliverable

Append a baseline section to `V3_1_1_HARDENING_REPORT.md`.

Do not fix findings yet.

## Gate

Proceed only if the repository still preserves the read-only architecture and no unrelated uncommitted change makes the baseline ambiguous.
