# v3 Fine-Comb Final File Audit

## 2026-08-31 remediation addendum

The original audit result was superseded by a live end-to-end finding: sensitive
column-profile minimum/maximum values could be persisted and copied to Git export.
The current implementation classifies and masks value-bearing profile evidence before
disk, audits profiles/distributions/samples independently, and repeats that audit before
Git export. Generated HTML rendering, action-card layout, package-install instructions,
and layman UI guidance were also repaired. Fresh live runs and exports are listed in
`V3_IMPLEMENTATION_REPORT.md`; historical runtime evidence remains user-owned and must
not be assumed safe.

Scope: operational project files after prompts 02–16. Historical `output/` and
`git_export/` evidence is user-owned runtime data and was not modified. Generated
`.egg-info`, virtual-environment, and cache files are non-authoritative build products
and are excluded from the source audit.

| File | Purpose | Entry/Callers | Reads | Writes (Local) | DB Access | Web Exposure | Issues | Status |
|---|---|---|---|---|---|---|---|---|
| `main.py` | Canonical launcher/router | User, BAT files | CLI arguments | None | Delegated only | Starts Web | None | PASS |
| `run_dashboard.bat` | Windows Web launcher | User | Local venv presence | None | None | Starts loopback Web | None | PASS |
| `run_metadata.bat` | Windows metadata launcher | User | Local venv presence | Real run only | Delegated read-only | None | None | PASS |
| `.env.example` | Non-secret v3 schema | Operator | None | None | None | Config only | Lowercase booleans; no credentials | PASS |
| `.gitignore` | Secret/runtime exclusions | Git | None | None | None | None | None | PASS |
| `pyproject.toml` | Package/test metadata | pip, pytest | None | Build metadata only | None | Static assets packaged | None | PASS |
| `requirements.txt` | Dependency lock input | pip | None | Environment only | None | Flask/renderers | None | PASS |
| `README.md` | Operator/developer guide | User | None | None | None | Documents Web | None | PASS |
| `OPERATOR_RUN_GUIDE.md` | Ordered safe rollout/recovery guide | Operator | None | None | None | Documents dashboard | One-DB-first sequence explicit | PASS |
| `HTML_FEATURE_CHECKLIST.md` | UI acceptance evidence | User/review | Web implementation/tests | This report only | None | Documents all UI surfaces | All required items verified | PASS |
| `RUNTIME_OUTPUT_CONTRACT.md` | Lazy output/export boundary | Operator/review | Runtime contracts | This report only | None | Documents browser roots | Evidence allowlist explicit | PASS |
| `SAFETY_MODEL.md` | Safety boundary | User/review | None | None | None | Documents controls | None | PASS |
| `V3_FILE_AUDIT.md` | Fine-comb source audit | User/review | Project files | This report only | None | None | Self-describing audit artifact | PASS |
| `V3_IMPLEMENTATION_REPORT.md` | Build/verification handoff | User/review | Verification results | This report only | None | Documents Web | Updated after final suite | PASS |
| `config/README.md` | Config boundary | User | None | None | None | None | None | PASS |
| `sql/README.md` | SQL asset policy | User | None | None | None | None | None | PASS |
| `src/mssql_database_documenter/__init__.py` | Package identity | Importers | None | None | None | None | None | PASS |
| `src/mssql_database_documenter/__main__.py` | Package CLI bridge | `python -m` | Arguments | None | Delegated only | None | None | PASS |
| `src/mssql_database_documenter/cli.py` | Controlled console workflows | Main/package entry | Env/query registries | Runs only after explicit command | Guarded SELECT only | None | No arbitrary command/SQL input | PASS |
| `src/mssql_database_documenter/config.py` | Typed dotenv/env settings | CLI/Web/runners | `.env`, process env | None | Connection config only | Loopback/single-job validation | None | PASS |
| `src/mssql_database_documenter/evidence_safety.py` | Independent evidence masking/secret audit | Run acceptance, Git export | Run evidence | None | None | Audit results displayed as JSON | Fails closed on raw classified values | PASS |
| `src/mssql_database_documenter/connection.py` | ODBC lifecycle | CLI/runners/API | Settings | Rollback/close only | `ApplicationIntent=ReadOnly` | Indirect | None | PASS |
| `src/mssql_database_documenter/safety.py` | Fail-closed SQL/cursor guard | Every query path | SQL text | None | Final execution boundary | Indirect | None | PASS |
| `src/mssql_database_documenter/redaction.py` | Secret-safe diagnostics | CLI/jobs/full run | Error text | None | None | Sanitizes errors/logs | None | PASS |
| `src/mssql_database_documenter/queries.py` | Core typed SELECT registry | CLI/inventory/full run | SQL Server catalogs | None | Guarded SELECT | No direct route | None | PASS |
| `src/mssql_database_documenter/programmable_queries.py` | Static code/dependency SELECT registry | CLI/full run | SQL catalogs/definitions | None | Guarded SELECT | No direct route | Definitions sanitized downstream | PASS |
| `src/mssql_database_documenter/contracts.py` | Output/evidence contracts | Full run/tests | None | None | None | Registry metadata | None | PASS |
| `src/mssql_database_documenter/metadata/__init__.py` | Reviewed query-catalogue boundary | Discovery/consumers | Query registries | None | SELECT definitions only | None | None | PASS |
| `src/mssql_database_documenter/profiling/__init__.py` | Fail-closed scan-threshold helpers | Full run/tests | Catalog estimates | None | None directly | None | Unknown/invalid estimates rejected | PASS |
| `src/mssql_database_documenter/relationships/__init__.py` | Relationship evidence vocabulary | Discovery/consumers | None | None | None | None | None | PASS |
| `src/mssql_database_documenter/lineage/__init__.py` | Lineage classification vocabulary | Discovery/consumers | None | None | None | None | None | PASS |
| `src/mssql_database_documenter/analysis/__init__.py` | Evidence/capability public boundary | Discovery/consumers | Contracts | None | None | None | None | PASS |
| `src/mssql_database_documenter/reporting/__init__.py` | Artifact-contract public boundary | Reporting/consumers | Contracts | None | None | None | None | PASS |
| `src/mssql_database_documenter/inventory.py` | Metadata-only runner | CLI | Catalog query results | Lazy manifested run | Guarded SELECT | Job API indirectly | `mkdir` occurs only after a real run starts | PASS |
| `src/mssql_database_documenter/fullrun.py` | Sequential discovery/profile/report pipeline | CLI/job API | Catalog/data evidence, project tests | Lazy run artifacts only | Guarded SELECT; thresholded scans | Job API indirectly | Fixed-argv pytest subprocess only; `shell=False`; no auto-export | PASS |
| `src/mssql_database_documenter/git_export.py` | Explicit sanitized handoff | Git-export API | One manifested run | Explicit Git root copy | None | POST API only | Containment + secret scan precede copy | PASS |
| `src/mssql_database_documenter/comparison/__init__.py` | Comparison public API | CLI compatibility/Web | Manifested snapshots | Explicit export only | None | Compare API | Supports 2/3 runs | PASS |
| `comparison/loaders.py` | Run/legacy summary loader | Engine/browser | Manifest, summaries, artifacts | None | None | Run registry | No source rewrite | PASS |
| `comparison/normalizers.py` | Stable CSV/text/number normalization | Loader/diff | Canonical CSV | None | None | Indirect | Full definitions retained | PASS |
| `comparison/diff.py` | 2/3-run timeline/deltas/diffs | Engine/tests | In-memory rows | None | None | Compare API | Missing evidence is explicit | PASS |
| `comparison/engine.py` | Category comparison orchestration | Compare API | Manifested run artifacts | None | None | Compare API | No causality/business-equivalence inference | PASS |
| `comparison/exporters.py` | HTML/CSV/JSON comparison export | Explicit compare action | Comparison result | Explicit unique export folder | None | POST compare action | No implicit export | PASS |
| `web/__init__.py` | Web package marker | Imports | None | None | None | Package only | None | PASS |
| `web/app.py` | Flask factory/loopback server | Main/tests | Settings/static assets | None on startup | None directly | Root application | Fixed URL browser open only | PASS |
| `web/security.py` | Host/origin/CSRF/header policy | Flask hooks | Request/session | Session cookie only | None | All routes | Strict loopback Host validation | PASS |
| `web/job_manager.py` | Single active job/status/log manager | APIs/dashboard | In-memory state | None outside target | Delegated | Job endpoints | Lock and terminal states verified | PASS |
| `web/file_browser.py` | Dual-root browser/run registry | Routes/APIs | Output/Git roots | None | None | Browser/file/run endpoints | Traversal and resolved-symlink containment | PASS |
| `web/renderers.py` | Safe evidence presentation | File page | Selected files | None | None | File preview | Large text/CSV streaming; large structured source fallback | PASS |
| `web/routes.py` | Human-facing pages/raw/download | Browser | Allowlisted contained files | None | None | GET routes | HTML raw served as text/plain | PASS |
| `web/api.py` | Predefined jobs/files/export API | Dashboard JS | Settings, manifests | Explicit runs/exports | Guarded delegated actions | `/api/*` | No arbitrary SQL/shell endpoint | PASS |
| `web/compare_api.py` | 2/3-run compare/filter/export API | Compare JS | Manifested runs | Explicit export only | None | `/api/compare` | Cache bounded to 10 comparisons | PASS |
| `web/templates/base.html` | Application shell/navigation | All pages | Render context | None | None | All pages | Persistent responsive navigation | PASS |
| `web/templates/dashboard.html` | Controls/jobs/run registry | Dashboard route | Sanitized config/job/run data | None | None | `/` | No secrets rendered | PASS |
| `web/templates/browser.html` | Root/folder listing | Browser route | Contained listing | None | None | `/browser` | Clear absent/empty states | PASS |
| `web/templates/file_view.html` | Evidence tables/source/paging | File route | Renderer output | None | None | `/file` | Badges and raw/download preserve evidence | PASS |
| `web/templates/run_detail.html` | Run metadata | Run route | Sanitized summary | None | None | `/run` | Partial/failed status represented | PASS |
| `web/templates/compare.html` | Compare selectors/filters/table | Compare route | Run registry | None | None | `/compare` | A/B required, C optional, paginated | PASS |
| `web/templates/error.html` | Sanitized error state | Error handlers | Safe message | None | None | Error responses | Internal exceptions not exposed | PASS |
| `web/static/js/dashboard.js` | Controlled action/poll/cancel/export client | Dashboard | API JSON | Predefined POSTs only | None directly | Browser client | CSRF and full-run confirmation | PASS |
| `web/static/js/browser.js` | Raw SQL copy/navigation helper | File page | Raw contained URL | Clipboard only | None | Browser client | Canonical raw source copied | PASS |
| `web/static/js/compare.js` | Compare/filter/paging client | Compare page | Compare APIs | Explicit export POST only | None | Browser client | 2/3-run logic and pagination | PASS |
| `web/static/css/app.css` | Core responsive presentation | All pages | None | None | None | Static asset | Sticky tables/readable code | PASS |
| `web/static/css/details.css` | Sidebar/badges/dark/print/detail styles | All/detail pages | None | None | None | Static asset | Print and responsive rules present | PASS |
| `tests/test_cli.py` | CLI dry-run regression | pytest | Registries | Temp/none | Mocked/none | None | None | PASS |
| `tests/test_config.py` | Env/default/validation tests | pytest | Temp dotenv | Temp only | None | Config validation | None | PASS |
| `tests/test_connection.py` | Read-only connection-string tests | pytest | Settings | None | No live DB | None | None | PASS |
| `tests/test_safety.py` | Forbidden-SQL/cursor tests | pytest | Test SQL | None | Fake cursor | None | None | PASS |
| `tests/test_inventory.py` | Lazy-run/path/query tests | pytest | Registries | Temp only | No live DB | None | None | PASS |
| `tests/test_fullrun.py` | Discovery/safety/sequence tests | pytest | Source/contracts | Temp only | Mocked/none | None | Threshold fail-closed covered | PASS |
| `tests/test_redaction.py` | Secret-redaction regressions | pytest | Test strings | None | None | Log/error safety | None | PASS |
| `tests/test_comparison.py` | 2/3-run/timeline/export tests | pytest | Temp manifested runs | Temp only | None | Engine/API contracts | Added/removed/changed/missing/mode/DB covered | PASS |
| `tests/test_file_browser.py` | Root/path/registry/export tests | pytest | Temp trees | Temp only | None | Browser boundaries | Symlink case may skip if OS denies creation | PASS |
| `tests/test_job_manager.py` | Lock/status/error/cancel tests | pytest | In-memory jobs | None | None | Job contract | None | PASS |
| `tests/test_renderers.py` | Complete/paginated/safe renderer tests | pytest | Temp evidence | Temp only | None | File renderer | Memory-bounded fallback covered | PASS |
| `tests/test_web_app.py` | Entry/lifecycle/security/API integration | pytest | Temp runs/assets | Temp only | Mocked connection only | Full local Web surface | Import/startup/dry-run laziness covered | PASS |

## Exact findings

| Finding | Exact location | Result |
|---|---|---|
| Read-only ODBC intent | `src/mssql_database_documenter/connection.py:23` | PASS |
| Fail-closed SQL validator | `src/mssql_database_documenter/safety.py:112` | PASS |
| Loopback Web validation | `src/mssql_database_documenter/config.py:176` | PASS |
| Host/origin/CSRF boundary | `src/mssql_database_documenter/web/security.py:34` | PASS |
| Predefined Web action allowlist | `src/mssql_database_documenter/web/security.py:13` | PASS |
| Path traversal/symlink containment | `src/mssql_database_documenter/web/file_browser.py:38` | PASS |
| Single-job conflict gate | `src/mssql_database_documenter/web/job_manager.py:58` | PASS |
| Comparison cache bound | `src/mssql_database_documenter/web/compare_api.py:29` | PASS |
| Unknown table sizes fail closed | `src/mssql_database_documenter/profiling/__init__.py:8` | PASS |
| Separate exact-count ceiling enforced | `src/mssql_database_documenter/fullrun.py:466` | PASS |
| Profile/sample/relationship thresholds | `src/mssql_database_documenter/fullrun.py:528`, `:623`, `:760` | PASS |
| Explicit-only Git export | `src/mssql_database_documenter/web/api.py:137` | PASS |
| Large-file formatted-view bound | `src/mssql_database_documenter/web/renderers.py:18` | PASS |
| Fixed subprocess, no shell/user command | `src/mssql_database_documenter/fullrun.py:1279` | PASS |
| Run manifest declares no implicit export | `src/mssql_database_documenter/fullrun.py:1437` | PASS |

## Targeted search result

- Eager `mkdir`: none on import, Web startup, dry-run, or connection check. Remaining calls are inside explicit real-run/export writers.
- Placeholder output generation: none.
- Shell execution, `shell=True`, `eval`, or runtime Python `exec`: none.
- Arbitrary command or arbitrary SQL endpoints: none.
- Unsafe path joins or unresolved symlink exposure: none found.
- Real credentials or hardcoded configured database names in source/config: none found. Test-only names are synthetic fixtures.
- `0.0.0.0`: rejection test only; runtime validation allows loopback hosts only.
- Concurrency: one active control/discovery/export job; comparison cache capped at ten.
- Unbounded browser reads: corrected; large text/CSV is streamed and oversized structured content becomes paginated source with raw/download retained.
- Omitted masking: credential data always redacted; sample persistence remains masked.
- Evidence truncation: none; UI pagination, raw view, and downloads retain canonical content.
- Two-run-only assumptions: none; A/B and optional C are implemented through engine, API, UI, and exports.

Overall result: **PASS**.

## Re-execution record — 2026-09-05

The instructions in `Prompts/SchoolERP_MSSQL_Documenter_v3_WebUI_Prompt_Pack/00_FINE_COMB_AUDIT_FINDINGS.md` were re-executed against the current implementation before starting `00_START_HERE.md`. The review was read-only except for adding this audit record.

| Required correction | Verification evidence | Result |
|---|---|---|
| Root entry point and Windows launchers | `main.py --help` exposes Web, connection-test, and controlled CLI modes; both launchers call the root entry point and contain no credentials | PASS |
| Lazy `output/` and `git_export/` behavior | Source search and regression tests confirm creation occurs only inside an explicit run/export; current folders contain manifested database evidence rather than build scaffolding | PASS |
| Shared CLI/Web discovery logic | CLI and Web job API both delegate real discovery to `fullrun.run_all` | PASS |
| Local Flask Web UI | `web/app.py`, configuration validation, and tests enforce loopback-only binding | PASS |
| Predefined actions only | `web/security.py` contains the closed action allowlist; arbitrary SQL and shell actions are absent | PASS |
| Single-job lifecycle | Locked `JobManager` exposes status, timestamps, database, mode, stage, progress, safe log tail, cancellation, and conflict rejection | PASS |
| Two/three-run comparison | Engine, API, UI, and tests support A/B plus optional C, including same- and cross-database warnings and pairwise deltas | PASS |
| Complete evidence rendering | Markdown, CSV, JSON, text/log/checksum, SQL, Mermaid, and trusted generated HTML renderers retain raw/download access and server-side pagination | PASS |
| Styled and canonical report access | Generated HTML has a styled view while raw source remains separately available | PASS |
| No presentation data loss | Large-file tests verify paginated/streamed views while raw and download routes retain the complete canonical file | PASS |
| Path containment | Absolute paths, traversal, and resolved symlink escapes are rejected for both output roots | PASS |
| Required Web regression coverage | Full suite covers binding, host/origin/CSRF security, allowlists, job locking, rendering, missing roots, comparison, large CSV, and safe export | PASS |

Execution evidence:

- Test suite: **86 passed, 2 skipped, 89 subtests**. The two skips are limited to symlink-escape cases when Windows does not grant symlink creation privilege; the containment logic and non-symlink traversal cases passed.
- Root entry point: **PASS** (`main.py --help`).
- Real output evidence: `Chikhali SchoolERP/run_20260831_181838` is `COMPLETED`, `full-readonly`, 20/20 stages, 0 warnings/errors, 1,042 files.
- Real output evidence: `Shirgaon SchoolERP/run_20260831_181928` is `COMPLETED`, `full-readonly`, 20/20 stages, 0 warnings/errors, 1,269 files.
- Git handoff evidence: a matching manifested export exists for each database run.

Re-execution result: **PASS — no unresolved finding blocks `00_START_HERE.md`.**

## Phase 16 sequential final-code review — 2026-09-05

The phase-16 fine-comb search was rerun after phases 02-15 completed. Authored project files remain covered by the main file table above. The following current files/build artifacts complete the inventory reconciliation:

| File | Purpose | Entry/Callers | Reads | Writes(Local) | DB Access | Web Exposure | Issues | Status |
|---|---|---|---|---|---|---|---|---|
| `src/mssql_database_documenter/web/templates/help.html` | Layman operator help and glossary | Help route/base navigation | Render context only | None | None | `/help` | None | PASS |
| `tests/test_evidence_safety.py` | Independent masking/secret-audit regression | pytest | Temporary manifested evidence | Temporary directory only | None | None | None | PASS |
| `src/mssql_database_documenter.egg-info/*` | Generated local packaging metadata | pip/editable install | Package metadata | Generated by packaging tools | None | None | Not authored runtime source; excluded by `.gitignore` | PASS |

Exact current findings:

| Review target | Exact location/evidence | Result |
|---|---|---|
| Eager directory creation | Production `mkdir` calls occur only inside `inventory.py`, `fullrun.py`, `comparison/exporters.py`, and `git_export.py` explicit writers | PASS |
| Placeholder/fake evidence | `fullrun.py:1312` is a negative acceptance assertion; HTML `placeholder` attributes are form hints only | PASS |
| Subprocess/shell | `fullrun.py:1297` uses a fixed pytest argument vector with `shell=False`; no runtime `shell=True`, `eval`, or Python `exec` | PASS |
| Arbitrary Web execution | Closed allowlist at `web/security.py:13`; no shell, SQL, eval, or Python execution route | PASS |
| Path joins/escapes | `web/file_browser.py:38-55` rejects absolute paths, parent traversal, resolved escapes, and symlink escapes | PASS |
| Secrets | `config.py:184-211`, `redaction.py`, job logging, and evidence safety audits sanitize credentials; no configured database/server credentials are hardcoded | PASS |
| Non-loopback binding | Runtime validation at `config.py:176-181`; `0.0.0.0` occurs only in rejection tests | PASS |
| Concurrency | `web/job_manager.py:58-65` holds a lock and rejects an unfinished current job | PASS |
| Bounded Web reads | `web/renderers.py:23`, `:58-99`, and `:103-126` cap formatted structured input and stream/paginate CSV/text | PASS |
| Masking | `fullrun.py:503-610`, `:612-669`, `evidence_safety.py`, and Git-export preflight mask and independently audit persistent values | PASS |
| Evidence truncation | Presentation pagination plus `/raw` and `/download` retain canonical full files; display-only recent-run/log-tail caps do not alter evidence | PASS |
| 2-run assumptions | Engine/API validate `{2, 3}` at `comparison/engine.py:95`, `comparison/diff.py:58`, and `web/compare_api.py:23` | PASS |
| Hardcoded database names | Production scan for the two configured database names returned zero matches | PASS |

Phase-16 test result: **86 passed, 2 skipped, 89 subtests**. Both skips require Windows symlink-creation privilege; all other security/path cases passed.

Phase-16 result: **PASS — no unresolved code-review finding.**
