# Prompt 02 — Baseline and Guardrails

## Objective
Freeze the real starting state and prove the repair begins without destructive changes.

## Actions
1. Record current branch, HEAD SHA, `git status --short`, Python/tool versions.
2. If HEAD differs from the audited SHA, compare first and preserve newer correct work.
3. Inspect launcher/config/connection/safety/fullrun/export/comparison/Web packages.
4. Verify no committed `output/` or `git_export/`.
5. Run only offline/lazy checks: imports, `main.py --help`, dry-run, current tests if installable.
6. Prove import/help/app-factory/dry-run create no output/export roots.
7. Search for `shell=True`, `os.system`, arbitrary subprocess, `eval`, runtime `exec`, direct unguarded `.execute(`, DML/DDL, credential files.

## Do not
Do not connect to MSSQL, create real runs/exports, delete historical runtime data, or modify code before baseline evidence is recorded.

## Deliverable
Create/update the Baseline section of `V3_1_REMEDIATION_REPORT.md`. STOP.
