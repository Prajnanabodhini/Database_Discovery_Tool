# Prompt 11 — Full Offline Regression and CI Gate

## Objective

Establish a clean, reproducible offline acceptance gate before any live MSSQL validation.

## Clean start

Ensure:
- no checked-in `.env`;
- no runtime `output/`;
- no runtime `git_export/`;
- no caches that affect result interpretation.

## Commands

Run:

```powershell
python -m compileall -q main.py src
python -c "import main; import mssql_database_documenter; import mssql_database_documenter.report_regeneration; import mssql_database_documenter.web.app"
python -m pytest -q -p no:cacheprovider -m "not live" tests
python main.py self-test
```

Also run dry-run SQL registry validation.

## Expected

- compile = PASS
- import = PASS
- pytest = 0 failed
- self-test = PASS
- no DB connection
- no runtime roots created
- all registered SQL = SAFE

## GitHub Actions gate

After approved code commit/push:

- Windows/Python 3.11 workflow must be **green**.
- Do not mark this prompt PASS from local tests alone.
- Record workflow run ID/URL, commit SHA and conclusion.

## Stop

If CI is red, do not start live DB validation.
