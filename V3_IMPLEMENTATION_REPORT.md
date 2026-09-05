# v3 Master Prompt Implementation Report

## 2026-08-31 repair verification

This report now includes the post-audit repair. Sensitive profile extrema are masked
before persistence, low-cardinality and sample evidence share the same policy, and an
independent evidence audit protects both run acceptance and Git export. Trusted HTML
reports render as sanitized body content; dashboard action cards no longer overlap; a
dedicated layman Help experience and contextual explanations cover every UI workflow.

Fresh sequential `full-readonly` runs completed for both configured databases:

- Chikhali SchoolERP: `run_20260831_181838`
- Shirgaon SchoolERP: `run_20260831_181928`

Both completed 20 stages with zero warnings/errors, zero masking-audit violations, and
zero checksum mismatches. Explicit sanitized Git exports were created for only these
two repaired runs. Earlier output/export runs were not changed and must not be treated
as safe merely because they contain an older checklist.

Scope: `00_START_HERE.md` -> `01_MASTER_REBUILD_OR_REPAIR_PROMPT.md`.

Historical `output/` and `git_export/` evidence was preserved. The original v3 build
created no runtime evidence; the later repair verification intentionally created the
two fresh live runs and corresponding audited Git exports listed above.

## Root and configuration

| File | Final implementation |
|---|---|
| `main.py` | Canonical source-checkout launcher; defaults to Web UI and delegates `web`, `test-connection`, and controlled `cli --mode` commands. |
| `run_dashboard.bat` | Starts the local dashboard through the project virtual environment. |
| `run_metadata.bat` | Starts the predefined metadata CLI workflow. |
| `.env.example` | Documents output/Git roots, loopback Web host/port, browser, one-job, and three-run settings without credentials. |
| `.gitignore` | Excludes `.env`, virtual environments, caches, build products, output, and Git exports. |
| `requirements.txt` | Reproducible runtime and test dependency list. |
| `pyproject.toml` | v0.3 packaging, Flask/renderer dependencies, Web templates/static package data, and pytest settings. |
| `README.md` | Exact installation, Web, CLI, lifecycle, comparison, safety, and test commands. |
| `SAFETY_MODEL.md` | Retains v2 database invariants and adds Web/API/job/path/export controls. |
| `config/README.md` | Declares the credential-free configuration boundary. |
| `sql/README.md` | Declares the reviewed query-registry/free-form-SQL boundary. |
| `V3_FILE_AUDIT.md` | Pre-implementation preserve/repair/refactor decision for every original source/config/test file. |

## Preserved and repaired discovery core

| File | Final implementation |
|---|---|
| `src/mssql_database_documenter/__init__.py` | v0.3 package identity. |
| `__main__.py` | Preserved package CLI delegation. |
| `cli.py` | Preserved staged, explicit, read-only console workflows. |
| `config.py` | Adds Web/Git settings, strict loopback validation, one-job validation, and sanitized diagnostics. |
| `connection.py` | Preserved explicit-database, timeout, rollback, read-only-intent connection behavior. |
| `contracts.py` | Adds `run_summary.json` and the styled HTML report to the evidence contract. |
| `fullrun.py` | Preserves v2 discovery; adds progress, boundary cancellation, truthful failed/cancelled partial manifests, lazy real-run lifecycle, HTML report, and removes automatic comparison/Git export. |
| `inventory.py` | Preserves metadata runner and adds v3 run summary/report-folder metadata. |
| `git_export.py` | New explicit-only, manifested-run, contained, secret-scanned Git handoff service. |
| `programmable_queries.py` | Preserved read-only programmable object and SQL Agent metadata catalogue. |
| `queries.py` | Preserved typed metadata query registry. |
| `redaction.py` | Preserved and reused for controlled Web job logs. |
| `safety.py` | Preserved fail-closed SQL validation and guarded cursor execution. |

## Comparison package

| File | Final implementation |
|---|---|
| `comparison/__init__.py` | Public 2/3-run API plus compatible explicit two-run export wrapper. |
| `comparison/loaders.py` | Loads only manifested output/Git runs and derives summaries for legacy evidence without rewriting it. |
| `comparison/normalizers.py` | Large-field CSV reading and stable text/numeric normalization. |
| `comparison/diff.py` | Stable identities, 2/3-run intervals/timelines, added/removed/changed states, numeric/percentage deltas, full definition sources, and unified diffs. |
| `comparison/engine.py` | Structural, programmable, size/profile, dependency, lineage, pipeline, risk/error, summary, quality, and coverage categories with mixed DB/mode warnings. |
| `comparison/exporters.py` | Explicit, unique HTML/CSV/JSON exports retaining numeric and definition evidence. |

## Web package

| File | Final implementation |
|---|---|
| `web/app.py` | Flask factory, loopback-only launcher, generated session secret, extensions, error handling, and optional browser open. |
| `web/security.py` | Same-origin mutation policy, session CSRF, action allowlist, CSP, clickjacking, MIME, referrer, and no-store headers. |
| `web/job_manager.py` | One-job lock, sanitized status/logs, progress, elapsed time, warnings, completion states, and boundary cancellation. |
| `web/file_browser.py` | Dual-root registry/browser with absolute/traversal/resolved/symlink containment checks and graceful missing roots. |
| `web/renderers.py` | Safe Markdown/HTML, complete JSON, paginated/searchable/sortable CSV, paginated text/SQL/Mermaid source, and raw fallback. |
| `web/routes.py` | Dashboard, output/Git browsers, safe preview, raw/download, run detail/checklist, and comparison pages. |
| `web/api.py` | Sanitized config, predefined actions, job state/cancel, file/run APIs, and explicit Git export; no arbitrary SQL or shell endpoint. |
| `web/compare_api.py` | Exact 2/3-run selection, in-memory result cache, filters/pagination, and explicit export. |
| `web/templates/*.html` | Responsive dashboard, browser, file renderer, run metadata, comparison, and safe error screens. |
| `web/static/css/*.css` | Local responsive styling, evidence tables, progress, and side-by-side definition layout. |
| `web/static/js/dashboard.js` | CSRF-protected predefined jobs, full-read-only confirmation, polling, cancellation, and explicit Git export. |
| `web/static/js/compare.js` | Run metadata, 2/3-run compare/export, filters, numeric deltas, and side-by-side definitions/diffs. |
| `web/static/js/browser.js` | Keyboard-friendly evidence navigation. |

## Tests

The original v2 tests remain. `test_comparison.py` was migrated to manifested v3 runs and expanded. New `test_file_browser.py`, `test_job_manager.py`, `test_renderers.py`, and `test_web_app.py` cover the master acceptance gate; `test_config.py` and `test_fullrun.py` add Web validation and truthful cancellation evidence.

Final prompt-21 result: **80 passed, 2 skipped, 88 subtests passed**. The skipped cases attempt to create Windows symlinks for browser and Git-export escape tests and are skipped only when the current identity lacks symlink permission; both resolved containment and explicit symlink rejection remain implemented.

Sequential prompts 02–21 additionally completed launcher hardening, fully lazy output/export lifecycle, Host-header validation, detailed jobs, symlink-safe evidence browsing, complete renderers, normalized run registry metadata, 2/3-run comparison timelines/UI, generic discovery evidence classes, fail-closed unknown-size profiling, a separate exact-count ceiling, persistent responsive navigation, comparison pagination, memory-bounded large-file previews, domain package boundaries, operator/UI/output contracts, a hardened evidence-only Git export, and a file-by-file final audit.

Additional verification:

- local Flask launch: PASS at `http://127.0.0.1:8765/`
- dashboard HTTP/CSP probe: PASS (HTTP 200)
- configured read-only connection check: PASS for both allowlisted databases
- dependency consistency (`pip check`): PASS
- arbitrary SQL/shell endpoint scan: none present
- new output/Git evidence during implementation: none
- Git working-tree diff: not available because this directory is not a Git repository

## Exact commands

```powershell
# Install
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Dashboard (default)
.\.venv\Scripts\python.exe main.py

# Dashboard without opening a browser
.\.venv\Scripts\python.exe main.py web --no-browser

# Read-only connection check
.\.venv\Scripts\python.exe main.py test-connection

# Controlled discovery modes
.\.venv\Scripts\python.exe main.py cli --mode metadata
.\.venv\Scripts\python.exe main.py cli --mode metadata+logic
.\.venv\Scripts\python.exe main.py cli --mode safe-profile
.\.venv\Scripts\python.exe main.py cli --mode full-readonly

# Tests
.\.venv\Scripts\python.exe -B -m pytest -q
```

## 2026-09-05 START_HERE re-execution

`00_START_HERE.md` and its required `01_MASTER_REBUILD_OR_REPAIR_PROMPT.md` were re-executed only after the fine-comb audit had passed. The existing implementation was audited and preserved in place; no replacement implementation and no fake discovery evidence were created.

Acceptance evidence:

- Root launcher help: PASS for `web`, `test-connection`, and controlled `cli` modes.
- Automated suite: **86 passed, 2 skipped, 89 subtests**. The two skips remain limited to Windows environments that do not grant the test process symlink-creation privilege.
- Dependency consistency: PASS (`No broken requirements found`).
- Read-only connection test: PASS for both configured databases. Server and login values were sanitized/redacted.
- Local Web launch: PASS at `http://127.0.0.1:8765/`; security headers were present.
- Live Web pages: PASS for dashboard, Help, Output browser, Git Export browser, Compare Runs, file preview, raw view, and download.
- Live renderer samples: PASS for Markdown, CSV, JSON, and trusted generated HTML. SQL, Mermaid, text/log, checksum, unsupported-file, large-file, and pagination branches pass their isolated/integration tests.
- Live path containment: PASS; a traversal request was rejected with HTTP 403.
- Live mutation controls: missing CSRF was rejected with HTTP 403; an arbitrary action was rejected with HTTP 400; the predefined dry-run completed with 100% progress and created no run evidence.
- Live comparison: PASS for two and three selected runs, output/Git-compatible evidence, mixed-database warning, pairwise intervals, and A/B/C numeric deltas.
- Existing real run evidence: both configured databases remain `COMPLETED`, `full-readonly`, 20/20 stages, with zero warning/error items, and each has a matching explicit Git export.
- Interactive visual-browser inspection was not claimed because no controllable browser was attached to this session. The live HTTP checks and Flask integration/browser-contract tests completed successfully.

Re-execution result: **PASS - all 19 master acceptance conditions are supported by current source, tests, live Web behavior, connection checks, and manifested real-run evidence. No corrective source-code change was required.**

## Complete prompt-pack sequential execution — 2026-09-05

All 23 prompts listed in the v3 pack manifest were first reviewed read-only, then executed one at a time in manifest order. No prompt began before its predecessor passed. The detailed per-prompt evidence is recorded in `Prompts/V3_PROMPT_PACK_SEQUENTIAL_EXECUTION_2026-09-05.md`.

Final result: **PASS**. Pack checksums, dependencies, 86 tests, 89 subtests, read-only access to both configured databases, the loopback Web surface, four real run-registry entries, and 4,618 runtime evidence checksums all pass. Two automated cases skip only because Windows did not grant symlink-creation privilege. No corrective production-code change was required.
