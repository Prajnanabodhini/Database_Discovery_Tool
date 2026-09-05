# Fine-Comb Audit Findings Against v2 Prompt Design

## Confirmed design issue 1 — no simple main launcher

The v2 master prompt required `src/mssql_database_documenter/cli.py` and module invocation, but did not require:

```text
main.py
```

at project root.

This makes first-run usability poor and allows the agent to create a package without an obvious entry point.

### v3 correction

Require:

```text
main.py
```

as the canonical launcher.

Supported behavior:

```bash
python main.py
python main.py web
python main.py cli --mode metadata
python main.py test-connection
```

`python main.py` should launch the local dashboard by default.

Also provide Windows convenience launchers:

```text
run_dashboard.bat
run_metadata.bat
```

They must call Python only and must not embed credentials.

---

## Confirmed design issue 2 — generated output folders created during build

The v2 prompt showed `output/` as part of project structure and required a `git_export/` layout.

This encourages an AI coding agent to create:

```text
output/
git_export/
```

plus nested documentation folders during project construction.

Those folders are supposed to represent generated evidence, not source scaffolding.

### v3 correction

Do NOT create any database/run output structure at project-build time.

It is acceptable for configuration to reference:

```text
OUTPUT_ROOT=output
GIT_EXPORT_ROOT=git_export
```

but these paths must be created lazily.

Rules:

- `output/` is created when the first real discovery run begins.
- `output/<database>/run_<timestamp>/` is created only for that actual run.
- `git_export/` is created only when the sanitized export operation is invoked.
- no fake `run_...` directories
- no placeholder database names
- no placeholder CSV/Markdown output files
- no fake manifests
- no `.gitkeep` required
- if folders do not exist, UI displays "No runs generated yet."

---

## Gap 3 — v2 explicitly said CLI only

The v2 master prompt said "CLI only", conflicting with the desired browser workflow.

### v3 correction

Provide both:

- CLI
- local Web UI

The UI is a client of the same application/service layer; it must not duplicate discovery logic.

---

## Gap 4 — static HTML cannot safely execute Python by itself

A browser-opened `file:///.../dashboard.html` cannot safely start local Python/database discovery.

### v3 correction

Use a local Flask application bound only to:

```text
127.0.0.1
```

The browser displays HTML from:

```text
http://127.0.0.1:<port>/
```

The web UI may call only predefined application actions.

Never expose a shell/command textbox.

---

## Gap 5 — no safe web execution control contract

v2 did not define how HTML-triggered execution should work.

### v3 correction

The UI must provide controlled buttons for:

- Test Connection
- Metadata
- Metadata + Logic
- Safe Profile
- Full Read-Only
- Generate Reports
- Create Git Export
- Compare Runs

Execution endpoints map to predefined Python functions/subcommands.

They must never accept arbitrary command strings.

---

## Gap 6 — no concurrency/resource protection

A user could accidentally launch multiple profiling jobs.

### v3 correction

Allow only one discovery job per configured SQL Server by default.

Display:

- idle/running/completed/failed/cancelled
- start time
- database
- mode
- current stage
- progress
- log tail

Reject conflicting starts.

---

## Gap 7 — comparison not sufficient

v2 primarily covered database comparison and future run-to-run diffing.

### v3 correction

Implement actual comparison of:

- 2 runs
- 3 runs

Allow:
- same DB over time
- different DBs
- output vs output
- sanitized Git-export metadata where compatible

Three-run UI should display:

```text
Run A | Run B | Run C
```

plus:
- A→B
- B→C
- A→C

where meaningful.

---

## Gap 8 — no complete HTML file renderer

### v3 correction

Browser must display:

- Markdown
- CSV
- JSON
- TXT
- SQL/T-SQL definitions
- log files
- Mermaid source/diagram where supported
- HTML reports
- checksums/manifests

Large CSVs must use server-side pagination/chunking.

---

## Gap 9 — "beautified" output was not explicitly specified

### v3 correction

Generate both:
1. canonical raw evidence files
2. styled HTML representation

Do not change or discard evidence to make it look better.

---

## Gap 10 — no explicit no-data-loss UI rule

### v3 correction

Every formatted view must retain access to:
- full source file
- every column
- every row through pagination/search
- original text/definition
- download/open-raw action

Summaries may supplement, never replace, source evidence.

---

## Gap 11 — no file-browser security model

### v3 correction

Prevent:
- `../`
- absolute path escape
- symlink escape
- access outside configured output/git-export roots

All browser file access must resolve and verify path containment.

---

## Gap 12 — no Web UI tests

### v3 correction

Test:
- localhost binding
- route authorization/session token
- path traversal
- predefined action whitelist
- job lock
- output rendering
- missing output roots
- 2-run compare
- 3-run compare
- large CSV pagination
- safe Git export
