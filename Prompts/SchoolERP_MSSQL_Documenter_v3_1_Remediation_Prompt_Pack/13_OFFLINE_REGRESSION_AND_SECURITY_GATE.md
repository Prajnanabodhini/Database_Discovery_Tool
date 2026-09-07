# Prompt 13 — Offline Regression and Security Gate

Run complete pre-live validation: compile, imports, help, self-test, dry-run, pytest, SQL registry validation, source unsafe-execution scan, Web tests, masking/export tests, comparison tests, report-regeneration tests.

Explicitly prove laziness for import, create_app, help, self-test, dry-run and in-memory comparison.

Review all subprocess/os.system/eval/exec/cursor.execute/file-copy/path-resolution/HTML paths. Confirm no arbitrary shell/SQL, unguarded cursor, network binding, secret echo or raw sensitive sample export.

Append exact evidence to `V3_1_REMEDIATION_REPORT.md`.

If any P0/P1 fails: STOP. No live DB.
