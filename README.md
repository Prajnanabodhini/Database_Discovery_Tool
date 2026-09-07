# SchoolERP MSSQL Documenter v3

A generic, strictly read-only SQL Server discovery and documentation engine with a localhost Flask dashboard, dual-root evidence browser, controlled jobs, and two/three-run comparison.

The v3 interface preserves the v2 discovery engine and evidence contract. It adds presentation and orchestration; it does not add arbitrary SQL, shell execution, stored-program execution, or database mutation.

## Current v3.1 validation status

**MSSQL DOCUMENTATION TOOL v3.1 — READY TO FREEZE.** Fresh ordered
metadata, metadata+logic, and safe-profile runs completed for both configured
databases on 2026-09-07 using release `0.3.1`. Both safe-profile masking audits and
independent re-audits passed with zero violations, including the DB1 column that
triggered the earlier containment failure. Explicit Git exports use the default
`exclude` policy, contain no sample payload CSVs or configured identity/credential
strings, and pass checksum verification. A three-run DB1 comparison and static HTML
export also passed. Each safe-profile run truthfully retains one non-fatal warning for
an existing broken view. The failed historical run remains local-only and unchanged.
Prompt 15 re-audited all 183 project-owned files, all named regression classes, the
offline quality gate, and the authorized live evidence with no unresolved P0/P1/P2.
This readiness declaration does not create a Git commit, tag, release, or deployment.

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

These commands start a new live read-only discovery and generate that run's normal reports:

```powershell
.\.venv\Scripts\python.exe main.py test-connection
.\.venv\Scripts\python.exe main.py cli --mode metadata
.\.venv\Scripts\python.exe main.py cli --mode metadata+logic
.\.venv\Scripts\python.exe main.py cli --mode safe-profile
.\.venv\Scripts\python.exe main.py cli --mode full-readonly
```

To regenerate only the presentation for an existing manifested run, use the
separate offline command. It does not connect to MSSQL or modify the selected run:

```powershell
.\.venv\Scripts\python.exe main.py regenerate-reports --run "output:School/run_20260907_120000"
```

Use `--database "Configured Name"` after the mode to select one database from the configured allowlist. `run_metadata.bat` is the metadata-mode shortcut.

The modes are cumulative but materially distinct:

- `metadata` reads structural catalogues only and performs no table/view data scans.
- `metadata+logic` adds stored definitions, static dependencies, and pipeline metadata;
  discovered code is never executed and table/view data is not scanned.
- `safe-profile` adds conservative bounded samples, profiles, sensitivity checks, and
  relationship validation under the safe thresholds.
- `full-readonly` adds separately configured larger sample/profile/distribution and
  relationship limits plus optional exact counts. Non-overridable hard ceilings still
  apply, and this mode requires an approved execution window.

Every run persists its effective `resolved_mode_policy` in run configuration, summary,
and manifest evidence, so the label can be checked against the work actually allowed.

Metadata runs catalogue database files and filegroups (without physical paths),
partition functions/schemes/compression, user-defined types, statistics, full-text
catalogues/indexes, CDC, Change Tracking, database-scoped configurations, and XML
schema collections. `MSSQL_FEATURE_SUPPORT_OVERVIEW.csv` and its Markdown companion
distinguish `PRESENT`, `ABSENT`, `INACCESSIBLE`, and `UNSUPPORTED`; `ABSENT` means
zero matching rows were visible to the reader, while SQL Server metadata visibility
can still limit scope. A missing or
unreadable catalogue is never silently reported as absent.

Security metadata is opt-in with `DISCOVER_SECURITY_METADATA=true` and defaults to
false. When enabled, the limited principal catalogue stores SHA-256 identity
fingerprints only. It does not export raw principal names, permission grants, or
credentials.

The legacy staged module CLI remains supported:

```powershell
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env dry-run
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env test-connection
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env inventory
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env --mode full-readonly all
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env --mode full-readonly discover-and-report
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env regenerate-reports --run "output:School/run_20260907_120000"
```

`all` and `discover-and-report` both perform a new live read-only discovery.
`regenerate-reports` is the offline selected-run operation. The ambiguous legacy
`report` command is intentionally not accepted.

## Sensitive-evidence safety note

Runs created before the 2026-08-31 profile-masking repair may contain raw minimum or
maximum values for columns later classified as sensitive. Keep historical `output/`
and `git_export/` runs local. Generate a new run and confirm that
`99_Git_Handoff/MASKING_SAFETY_AUDIT.json` reports `PASS` before creating or sharing a
new Git export. This warning also applies to failed run `20260906_150848`; it predates
the final-classification reconciliation repair. The exporter repeats the audit and
rejects unsafe evidence.

## Output lifecycle

- Importing, installing, testing, or launching the dashboard does not create run evidence.
- A real discovery action creates `output/<database>/run_<timestamp>/` lazily.
- Completed and partial runs contain `00_Run_Metadata/manifest.json` and `run_summary.json`.
- **Regenerate Reports** selects one manifested output run and creates a separate
  versioned Markdown/HTML presentation under `output/report_regenerations/`. It
  reads canonical artifacts only, makes no MSSQL connection, verifies source hashes
  before and after, and never overwrites the source or an earlier regeneration.
- Comparison results stay in memory unless **Compare and export** is selected.
- A Git export is created only through the explicit Git-export action and is rescanned for configured sensitive values before copying.
- Local output is canonical working evidence and can retain policy-approved profile extrema or distribution labels. It is not automatically safe to publish.
- Git export applies the separate `GIT_EXPORT_PROFILE_VALUE_POLICY`. The secure default, `mask_unknown_text`, pseudonymizes unknown textual profile values and redacts binary values in the staged copy; `aggregate_only` withholds extrema and distribution labels while retaining counts and aggregate metrics. A `raw` profile-value policy is not supported.
- Git-export masking is a conservative publication boundary, not proof that every local value has been semantically de-identified. Review `99_Git_Handoff/GIT_EXPORT_POLICY.json`, the independent audit result, and checksums before committing an export.
- Existing historical `output/` and `git_export/` evidence is never treated as source scaffold or silently replaced.

## Dashboard capabilities

The dashboard shows sanitized connection settings and safety controls; starts only predefined discovery actions; regenerates presentation reports offline from a selected manifested output run; provides live, redacted progress and stage-boundary cancellation; browses output and sanitized Git-export roots; renders Markdown, CSV, JSON, text, SQL, Mermaid source, and trusted generated HTML; retains raw/download access; and compares two or three manifested runs.

Report regeneration is not database discovery and is not a Git handoff. It cannot
refresh metadata or fill evidence gaps. Its new folder contains a regeneration
manifest and checksums, while the selected canonical run remains byte-for-byte
unchanged. Use a new discovery run when current database evidence is required, and
use the separate audited Git-export action when a reviewed handoff is required.

Comparison supports same-database history, cross-database structure, mode warnings,
stable object identities, interval/timeline statuses, numeric and percentage deltas,
definition diffs, filters, pagination, and explicit HTML/CSV/JSON export. Status filters
use the complete A-to-B, B-to-C, and A-to-C event history, so added-then-changed,
reverted, and remove/re-add histories remain visible under every applicable filter.
Global totals cover every category row; category totals cover that category or its
current filtered rows. Primary-status totals add up to row counts, while interval/event
occurrences may exceed row counts because one object can have several events.

JSON and CSV are the canonical machine-readable comparison outputs. Exported HTML is a
fully server-rendered human-readable report containing run metadata, warnings, scoped
summaries, category rows, A/B/C evidence, interval statuses, timeline events, numeric
deltas, and definition diffs. It contains no script dependency and remains useful after
the safe browser renderer removes styling.

Comparison never executes discovered definitions or infers causality.

## Production precautions

Read [SAFETY_MODEL.md](SAFETY_MODEL.md) before connecting. Begin with dry-run and metadata mode. Full read-only profiling cannot modify the database but can consume meaningful CPU, I/O, locks, and network capacity. Use a dedicated least-privilege reader, thresholds, timeouts, masking, and a suitable maintenance window.

## Tests

Runtime discovery never launches pytest and does not require pytest or the `tests/`
source tree. Stage 21 checks only the current run, registered SQL, runtime source, and
artifact contracts. Developer tests are a separate, explicit offline command:

```powershell
.\.venv\Scripts\python.exe main.py self-test
```

The environment-independent spelling, and local equivalent of the GitHub CI quality
gate, is `python main.py self-test`.

`self-test` bypasses `.env` loading, makes no MSSQL connection, and does not create a
discovery run or Git export. It invokes only the fixed offline pytest command, excludes
tests marked `live`, disables pytest cache creation, and returns a sanitized summary.
Pytest is an optional development dependency; its absence cannot prevent discovery.
The Web UI intentionally exposes no self-test action, keeping developer validation out
of the runtime job surface.

The underlying developer command remains available when detailed pytest output is
needed:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q
```

The suite exercises the v2 fail-closed SQL controls and the v3 launcher, lazy lifecycle, Web security, containment, renderers, registry, job lock/cancellation, Git export, and two/three-run comparison.

GitHub runs the same offline regression scope on Windows with Python 3.11. The CI gate
installs the test dependencies, compiles and imports the application, excludes tests
marked `live`, and fails if repository-level `output/` or `git_export/` evidence is
created. It receives no MSSQL credentials or production secrets.
