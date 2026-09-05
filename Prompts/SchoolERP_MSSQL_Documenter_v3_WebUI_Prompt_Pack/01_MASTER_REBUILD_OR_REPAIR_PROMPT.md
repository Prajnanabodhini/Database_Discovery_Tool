# MASTER PROMPT — Rebuild/Repair the Generic MSSQL Documenter with Web UI and 3-Run Comparison

You are working on a Python project whose purpose is comprehensive, read-only discovery and documentation of Microsoft SQL Server databases.

If a previous implementation already exists:
1. inspect every file first,
2. create a file-by-file audit,
3. preserve good working modules,
4. repair incomplete/incorrect implementation,
5. do not generate fake discovery output during development.

If no implementation exists, create it.

Project name:

`mssql_database_documenter`

The implementation must be generic and database-agnostic.

---

# 1. Mandatory top-level launchers

Create at project root:

```text
main.py
run_dashboard.bat
run_metadata.bat
```

`main.py` is the canonical application entry point.

Required behavior:

```bash
python main.py
```

Launch local Web UI and optionally open browser.

```bash
python main.py web
```

Same explicit web mode.

```bash
python main.py test-connection
```

Run safe connection test from console.

```bash
python main.py cli --mode metadata
python main.py cli --mode metadata+logic
python main.py cli --mode safe-profile
python main.py cli --mode full-readonly
```

The top-level launcher must delegate to package code. Business/discovery logic must not live in `main.py`.

---

# 2. Do not create run/output evidence at build time

This is mandatory.

During project generation, DO NOT create:

```text
output/
git_export/
output/<database>/
output/<database>/run_.../
git_export/MSSQL/<database>/
```

unless the folder already exists from real historical runs.

Do not create placeholder CSV, JSON, Markdown, manifests, sample outputs, fake database directories, or fake runs.

Configuration may contain:

```env
OUTPUT_ROOT=output
GIT_EXPORT_ROOT=git_export
```

but directories are lazy.

Create `output` only when an actual discovery run starts.

Create a run directory only after:
- configuration validates,
- database is selected,
- execution is actually started.

Create `git_export` only when a user runs the Git Export action.

The Web UI must work correctly when neither folder exists.

---

# 3. Web architecture

Use Flask for the local web application unless the existing project already has an equally suitable lightweight framework.

Required:

```text
src/mssql_database_documenter/web/
├── app.py
├── routes.py
├── api.py
├── job_manager.py
├── file_browser.py
├── renderers.py
├── compare_api.py
├── security.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── browser.html
│   ├── file_view.html
│   ├── compare.html
│   ├── run_detail.html
│   └── error.html
└── static/
    ├── css/
    │   └── app.css
    └── js/
        ├── dashboard.js
        ├── browser.js
        └── compare.js
```

Do not require internet/CDN access for core operation.

---

# 4. Web server safety

Bind by default only to:

```text
127.0.0.1
```

Do not bind to `0.0.0.0` by default.

Do not expose the dashboard to LAN/internet by default.

Add:

```env
WEB_HOST=127.0.0.1
WEB_PORT=8765
WEB_AUTO_OPEN_BROWSER=true
```

Implement an application-generated session/CSRF token.

Only same-origin requests may trigger actions.

Do not implement an arbitrary shell/SQL textbox.

---

# 5. Web dashboard

The landing dashboard must show:

## Connection panel
- configured server alias/sanitized server
- configured database(s)
- connection mode
- current discovery mode
- mask-sensitive-data state
- sample row setting
- exact row count state
- query timeout

Never display password.

## Safety status
- read-only guard status
- last safety-test result
- masking enabled?
- localhost-only?
- active job?

## Execution controls
Buttons:
- Dry Run
- Test Connection
- Metadata
- Metadata + Logic
- Safe Profile
- Full Read-Only
- Generate/Refresh Reports
- Create Git Export

Each button maps only to a predefined internal action.

`Full Read-Only` requires a confirmation dialog explaining possible resource impact.

## Live execution
Show:
- job ID
- database
- mode
- status
- start time
- elapsed time
- current stage
- progress
- warnings
- live/recent log lines

Use polling or Server-Sent Events.

Do not execute more than one heavy discovery job concurrently by default.

---

# 6. Output browser

The HTML UI must browse both logical roots:

```text
Output
Git Export
```

If missing:

```text
No output runs generated yet.
No Git exports generated yet.
```

Display tree navigation:

```text
Database
  Run
    Folder
      File
```

Provide:
- breadcrumbs
- search
- extension/type filter
- file size
- modified date
- open
- raw view
- download/copy where appropriate

Do not expose anything outside configured roots.

---

# 7. File rendering

Implement renderers for:

## Markdown
Render headings, tables, code blocks, links and callouts safely.

## CSV
Display as styled table with:
- all columns
- server-side or chunked pagination
- search
- sort
- column filters where practical
- row count
- visible range
- raw/download access

Never truncate the underlying evidence.

## JSON
Pretty formatted expandable/tree-like rendering where practical, plus raw view.

## TXT/LOG
Monospace formatted, search, line numbers for large text where practical.

## SQL/T-SQL definition text
Syntax-style formatting, line numbers, copy/raw access.

## Mermaid
If local Mermaid rendering is packaged safely, render diagram and offer source.
If not, show styled source and optional pre-generated SVG/PNG.

## HTML
Render only trusted project-generated HTML.
Do not blindly execute arbitrary scripts from discovered files.

Unsupported files get metadata + raw/download option.

---

# 8. Beautified output without data loss

Canonical evidence remains:

```text
CSV
JSON
Markdown
TXT
SQL-definition text
manifest/checksums
```

Generate a styled HTML presentation layer in addition.

Do not replace raw evidence.

Every summary card/table must allow drilling to full evidence.

Do not:
- drop rows,
- drop columns,
- silently round values,
- change IDs,
- hide NULLs,
- rewrite definitions.

For very large data, paginate; do not truncate.

---

# 9. Run index

Every completed or partially completed real run must have:

```text
manifest.json
run_summary.json
```

and be indexed by the application.

Create a run registry by scanning actual output directories rather than maintaining a fragile external DB unless clearly justified.

Display runs with:
- run ID
- database
- server alias
- timestamp
- mode
- status
- tool version
- SQL Server version
- row/sample settings
- completion coverage
- warning/error count

---

# 10. Comparison UI — 2 or 3 runs

Create a comparison page.

User must be able to select:

```text
Run A
Run B
optional Run C
```

Require at least 2 and maximum 3.

Allow:
- same database across time
- different databases
- different discovery modes, with warning
- output runs
- compatible Git exports where metadata supports comparison

Show run metadata before comparison.

---

# 11. Three-run comparison

For 3 runs display:

```text
Metric/Object | Run A | Run B | Run C | A→B | B→C | A→C
```

Comparison categories:

- database summary
- schemas
- tables
- columns
- data types
- PKs
- FKs
- inferred relationships
- indexes
- constraints
- views
- stored procedures
- functions
- triggers
- synonyms
- sequences
- row counts
- table sizes
- table shapes
- definition hashes
- dependency edges
- lineage edges
- pipeline catalogue
- data quality
- risks
- coverage/errors

---

# 12. Comparison semantics

Use stable comparison keys.

Examples:

Table:
```text
database + schema + table
```

Column:
```text
database + schema + table + column
```

Procedure:
```text
database + schema + procedure
```

For same-DB historical comparison, database can be part of identity but does not need to differ.

Statuses:

```text
UNCHANGED
ADDED
REMOVED
CHANGED
NOT_AVAILABLE
NOT_COMPARABLE
```

For three-run timeline, identify patterns such as:

```text
ADDED_IN_B
REMOVED_IN_C
CHANGED_A_TO_B
CHANGED_B_TO_C
CHANGED_BOTH_INTERVALS
REVERTED_TO_A
```

Do not infer causality.

---

# 13. Numeric deltas

For numeric metrics show:

```text
A
B
C
B-A
C-B
C-A
percentage changes where denominator is valid
```

Examples:
- row estimate
- reserved MB
- used MB
- index MB
- orphan count
- null %
- distinct count

Clearly label estimated vs exact.

---

# 14. Definition comparison

For views/procedures/functions/triggers:

Use normalized definition hashes.

If hash differs:
- show changed status
- provide side-by-side textual diff
- for 3 runs allow A vs B, B vs C, A vs C

Do not execute code.

---

# 15. Comparison filtering

UI filters:
- Changed only
- Added
- Removed
- Unchanged
- Errors/warnings
- schema
- object type
- severity
- database

Allow export of comparison results as:
- HTML
- CSV
- JSON

Generated comparison files are real outputs and should be created only when user invokes comparison/export.

---

# 16. Git-export browser

Git Export must be browsable through the same HTML interface.

The app should display a badge indicating:

```text
SANITIZED GIT EXPORT
```

Provide safe-to-commit checklist status.

Do not allow the UI to reveal files intentionally excluded from the export.

---

# 17. Execution from HTML

Static HTML cannot directly run Python safely.

Therefore HTML buttons call local Flask API endpoints.

Example internal endpoints:

```text
POST /api/jobs/dry-run
POST /api/jobs/test-connection
POST /api/jobs/start
POST /api/jobs/cancel
GET  /api/jobs/current
GET  /api/jobs/<id>
GET  /api/jobs/<id>/events

GET  /api/runs
GET  /api/files
GET  /api/file

POST /api/compare
POST /api/git-export
```

Do not expose raw command execution.

All action arguments must be validated against strict enums/configured database names.

---

# 18. Job manager

Implement one controlled job manager.

Features:
- one heavy discovery job at a time by default
- sequential DB processing
- clean status lifecycle
- cancellation support where safe
- exception capture
- partial-run preservation
- logs
- no fake success

Statuses:

```text
QUEUED
RUNNING
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
CANCELLED
```

Cancellation means stop future discovery stages/close connection; no DB rollback semantics are needed because DB is read-only.

---

# 19. Existing discovery requirements remain

Retain all good v2 requirements:

- generic .env database selection
- sequential multi-DB processing
- read-only guard
- metadata
- schemas/tables/columns
- PK/FK/constraints/indexes
- table sizes/shape
- profiling
- safe samples
- PII masking
- views
- procedures/functions/triggers
- synonyms/sequences
- extended properties
- SQL Agent metadata
- declared and inferred relationships
- cardinality/orphans
- lineage
- pipeline candidates
- cross-database/cross-server references
- data-quality analysis
- structural classification
- manifests/checksums
- definition hashes
- Git-safe export
- evidence FACT/DATA_VALIDATION/INFERENCE/UNKNOWN language

Do not weaken those requirements.

---

# 20. Project structure

Target:

```text
mssql_database_documenter/
├── main.py
├── run_dashboard.bat
├── run_metadata.bat
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
├── src/
│   └── mssql_database_documenter/
│       ├── cli.py
│       ├── config.py
│       ├── connection.py
│       ├── safety.py
│       ├── discovery/
│       ├── metadata/
│       ├── profiling/
│       ├── relationships/
│       ├── lineage/
│       ├── analysis/
│       ├── reporting/
│       ├── comparison/
│       │   ├── engine.py
│       │   ├── loaders.py
│       │   ├── normalizers.py
│       │   ├── diff.py
│       │   └── exporters.py
│       └── web/
│           ├── app.py
│           ├── api.py
│           ├── job_manager.py
│           ├── file_browser.py
│           ├── renderers.py
│           ├── compare_api.py
│           ├── security.py
│           ├── templates/
│           └── static/
├── tests/
└── sql/
```

Notice: `output/` and `git_export/` are intentionally absent from source scaffold.

---

# 21. Tests

In addition to v2 safety tests, test:

- `python main.py --help`
- `python main.py` launcher wiring without DB execution
- missing output root
- missing git-export root
- lazy run folder creation
- no placeholder output files
- localhost-only default
- CSRF/session token
- execution action whitelist
- invalid database rejection
- path traversal
- symlink/root escape
- file rendering
- large CSV pagination
- Markdown rendering
- JSON rendering
- SQL text rendering
- run registry
- 2-run comparison
- 3-run comparison
- A/B/C numeric deltas
- procedure hash change
- added/removed objects
- mixed DB warning
- job lock
- cancellation
- Git-export browsing
- no data-loss/raw-source access

---

# 22. Acceptance gate

Do not declare completion until:

1. root `main.py` exists and works,
2. Web UI launches locally,
3. CLI still works,
4. no output/git_export is pre-created by build,
5. first real run creates output lazily,
6. Git export is created only on explicit action,
7. Web UI browses both roots,
8. core file types render correctly,
9. formatted UI retains raw/full evidence access,
10. predefined discovery can be started through HTML,
11. no arbitrary command execution exists,
12. one-job concurrency protection works,
13. 2-run comparison works,
14. 3-run comparison works,
15. same-DB historical diff works,
16. cross-DB compare works,
17. security/path tests pass,
18. existing read-only DB safeguards remain intact,
19. all automated tests pass.

At the end, provide a file-by-file implementation report and exact run commands.
