# Prompt 12 — CI and Developer Quality Gate

## Objective
Enforce offline regressions independently on GitHub.

Add `.github/workflows/test.yml`:
- checkout
- supported Python (prefer Windows/operator parity)
- install test dependencies
- compile/import sanity
- pytest
- assert repository `output/` and `git_export/` were not created

No live MSSQL and no production secrets. Document `python main.py self-test` as local equivalent.

STOP.
