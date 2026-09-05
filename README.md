# SchoolERP MSSQL Documenter v3

A generic, strictly read-only SQL Server discovery and documentation engine with a localhost Flask dashboard, dual-root evidence browser, controlled jobs, and two/three-run comparison.

The v3 interface preserves the v2 discovery engine and evidence contract. It adds presentation and orchestration; it does not add arbitrary SQL, shell execution, stored-program execution, or database mutation.

## Install

Python 3.11 or newer is required. From this project directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

The editable project installation is required for both `main.py` and the documented
`python -m mssql_database_documenter` commands. It installs the runtime dependencies
and test runner declared in `pyproject.toml`.

Copy `.env.example` to `.env`, configure only explicitly approved databases, and keep `.env` local. The Web UI itself can launch without a live database connection.

For the first live validation, configure exactly one database and follow the ordered
[Operator Run Guide](OPERATOR_RUN_GUIDE.md): Dry Run, Test Connection, Metadata and
review, Metadata + Logic and review, Safe Profile and review, then explicit Git export.
Add multiple databases only after this sequence succeeds.

## Launch the local dashboard

```powershell
.\.venv\Scripts\python.exe main.py
```

Equivalent commands:

```powershell
.\run_dashboard.bat
.\.venv\Scripts\python.exe main.py web
.\.venv\Scripts\python.exe main.py web --no-browser
```

The server rejects non-loopback `WEB_HOST` values. The default address is `http://127.0.0.1:8765/`.
Never expose the dashboard to a network interface without a separate security review.

## Safe console commands

```powershell
.\.venv\Scripts\python.exe main.py test-connection
.\.venv\Scripts\python.exe main.py cli --mode metadata
.\.venv\Scripts\python.exe main.py cli --mode metadata+logic
.\.venv\Scripts\python.exe main.py cli --mode safe-profile
.\.venv\Scripts\python.exe main.py cli --mode full-readonly
```

Use `--database "Configured Name"` after the mode to select one database from the configured allowlist. `run_metadata.bat` is the metadata-mode shortcut.

The legacy staged module CLI remains supported:

```powershell
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env dry-run
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env test-connection
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env inventory
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env --mode full-readonly all
```

## Sensitive-evidence safety note

Runs created before the 2026-08-31 profile-masking repair may contain raw minimum or
maximum values for columns later classified as sensitive. Keep historical `output/`
and `git_export/` runs local. Generate a new run and confirm that
`99_Git_Handoff/MASKING_SAFETY_AUDIT.json` reports `PASS` before creating or sharing a
new Git export. The exporter repeats this audit and rejects unsafe evidence.

## Output lifecycle

- Importing, installing, testing, or launching the dashboard does not create run evidence.
- A real discovery action creates `output/<database>/run_<timestamp>/` lazily.
- Completed and partial runs contain `00_Run_Metadata/manifest.json` and `run_summary.json`.
- Comparison results stay in memory unless **Compare and export** is selected.
- A Git export is created only through the explicit Git-export action and is rescanned for configured sensitive values before copying.
- Existing historical `output/` and `git_export/` evidence is never treated as source scaffold or silently replaced.

## Dashboard capabilities

The dashboard shows sanitized connection settings and safety controls; starts only predefined discovery actions; provides live, redacted progress and stage-boundary cancellation; browses output and sanitized Git-export roots; renders Markdown, CSV, JSON, text, SQL, Mermaid source, and trusted generated HTML; retains raw/download access; and compares two or three manifested runs.

Comparison supports same-database history, cross-database structure, mode warnings, stable object identities, interval/timeline statuses, numeric and percentage deltas, definition diffs, filters, pagination, and explicit HTML/CSV/JSON export. It never executes discovered definitions or infers causality.

## Production precautions

Read [SAFETY_MODEL.md](SAFETY_MODEL.md) before connecting. Begin with dry-run and metadata mode. Full read-only profiling cannot modify the database but can consume meaningful CPU, I/O, locks, and network capacity. Use a dedicated least-privilege reader, thresholds, timeouts, masking, and a suitable maintenance window.

## Tests

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q
```

The suite exercises the v2 fail-closed SQL controls and the v3 launcher, lazy lifecycle, Web security, containment, renderers, registry, job lock/cancellation, Git export, and two/three-run comparison.
