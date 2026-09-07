# SchoolERP MSSQL Documenter v3.1 - Final Fine-Comb File Audit

## Current decision - 2026-09-07 Prompt 15 rerun

**MSSQL DOCUMENTATION TOOL v3.1 — READY TO FREEZE.**

The earlier `NOT READY TO FREEZE` decision remains below as historical evidence of
the defects that correctly stopped the first review. The final sections document the
repairs, live revalidation, and complete rerun that supersede that historical verdict.

Recorded: 2026-09-06  
Repository: `Prajnanabodhini/Database_Discovery_Tool`  
Branch: `main`  
Starting HEAD: `1c608d12d7c0f107931144dbbdc4e536865ab546`  
Audit interpreter: project `.venv`, Python 3.13.14  
Working tree: pre-existing remediation work is uncommitted; 73 status entries were present at audit capture

## Decision

**NOT READY TO FREEZE.**

The code/offline gate passes, but the authorized live DB1 safe-profile gate failed
closed. One column-profile maximum was persisted while the column was classified
`Unknown`; later bounded sample analysis upgraded the same column to high-confidence
PII, and the earlier value was not reconciled/remasked. The final evidence audit
correctly stopped run `20260906_150848`.

No `MSSQL DOCUMENTATION TOOL v3.1 - READY TO FREEZE` declaration is made.

Additional P2: distribution and runtime evidence still identify the implementation
as `0.3.0`, not a reviewed v3.1/0.3.1 release. This was not explicitly accepted.

## Scope and method

The audit covers 182 project-owned files after creation of this document:

- 65 implementation files under `src/` (52 Python modules and 13 Web assets);
- 25 test files;
- 7 configuration, packaging, ignore-policy, and CI files;
- 12 root entry, launcher, and documentation files that existed at audit start;
- this final audit document;
- 72 prompt/specification files under `Prompts/`.

Generated `output/`, generated `git_export/`, `.venv/`, caches, bytecode, build
products, `.git/`, and the secret-bearing local `.env` are runtime or environment
state, not project-owned source. They were excluded from the file-purpose matrix.
The three new Prompt 14 runs were inspected separately as live evidence.

For every implementation-owned file, the audit considered purpose/owner, callers,
reads, local writes, database access, Web exposure, safety boundary, applicable
tests, and current status. Static searches covered all regression classes named by
Prompt 15. Prompt-pack checksum manifests were independently recalculated.

Status vocabulary:

- `PASS`: implementation and current evidence satisfy the reviewed responsibility;
- `HISTORICAL`: retained evidence/document, not current acceptance proof;
- `P1`: freeze-blocking defect;
- `P2`: must be repaired or explicitly accepted before freeze;
- `BLOCKED`: cannot be executed because an earlier required live gate failed.

## Freeze blockers

| Severity | Finding | Exact evidence | Required resolution |
|---|---|---|---|
| P1 | Late sensitivity classification is not reconciled back into persisted column profiles | Live DB1 safe-profile run `20260906_150848`: `unmasked PII value in COLUMN_PROFILE.csv row 213, field maximum_value`; affected identity `dbo.FeeMstStudent.outwardno`; raw value intentionally not reproduced | Reconcile the final strongest category across profile, low-cardinality, and sample artifacts before persistence/finalization; remask from an in-memory safe source or avoid persisting extrema until classification is final; add an end-to-end regression; create a fresh DB1 run |
| P2 | Release identity remains `0.3.0` | `pyproject.toml`, package `__version__`, inventory manifest, and reporting manifest hard-code `0.3.0` | Choose one reviewed v3.1 release version and source it from one location; update package/evidence contracts and tests |
| Live gate | DB1 did not pass; therefore DB2 and three-run smoke are prohibited | Prompt 14 report section; DB2/comparison/export were not run | After P1 repair and offline pass, rerun Prompt 14 from DB1 dry-run in order |

## Named regression search results

| Prompt 15 search | Result | Evidence/conclusion |
|---|---|---|
| Eager `mkdir` / startup output-export | PASS | Imports, help, self-test, dry-run and `create_app` laziness tests pass; creation is confined to real runs or explicit guarded exports/regenerations |
| Arbitrary SQL / unguarded cursor | PASS | Registry suite passes; execution sites use `ReadOnlyCursor` and final-boundary validation; `executemany` is denied |
| Discovered-code execution | PASS | Stored SQL and Agent commands are parsed as text only; no stored procedure, job, PowerShell, CmdExec or SSIS execution path exists |
| Shell / unsafe subprocess | PASS | Only explicit self-test uses subprocess, with constant argv, `shell=False`, timeout, controlled cwd and sanitized summary; no `os.system`, `eval` or production `exec` |
| Secrets / raw samples | **P1** | Git export remains fail-closed and sample values passed their masking check, but one late-classified PII profile maximum remained unmasked in local failed evidence |
| Misleading reports action | PASS after doc correction | Web action is selected-run, offline, versioned report regeneration; checklist wording was corrected from “Generate Reports” |
| Script-dependent comparison HTML | PASS | Exporter produces static escaped HTML; safe renderer tests confirm evidence survives script removal |
| Safe/full mode aliasing | PASS offline | Resolved policies and tests prove distinct limits/branches; full-readonly live work was not authorized |
| SQL Agent execution | PASS | Raw command is internal-only analysis input; persisted output is sanitized references/hash/classification; analyzers contain no execution primitive |
| Monolithic leftovers | PASS with maintainability note | `fullrun.py` is 364 lines and is primarily lifecycle/orchestration; domain mixins own profiling, lineage, relationships, analysis and reporting. Several domain files exceed 300 lines but are cohesive, not freeze blockers |
| Runtime pytest coupling | PASS | Production discovery writes semantic review evidence and never invokes pytest; pytest exists only behind explicit `main.py self-test` and CI |
| Missing MSSQL metadata contracts | PASS | Required query families, feature states, artifacts, output contracts and comparison registrations exist and pass tests |
| Two-run-only assumptions / three-run gaps | PASS | Exactly 2/3 runs, A-B/B-C/A-C events, multi-event filtering, summary scopes and raw links are covered |
| Missing CI | PASS | `.github/workflows/test.yml` runs Windows/Python 3.11 compile/import/offline tests and asserts runtime roots remain absent |
| Destination/path containment | PASS | Shared component guard covers Git, comparison and regeneration destinations; real Windows junction regressions pass |

## Root, configuration, CI and documentation files

| File | Purpose and callers | Reads / writes / DB / Web | Safety, tests and status |
|---|---|---|---|
| `main.py` | Canonical launcher; operator and batch callers | Reads CLI/env-file path; dispatch only; no direct DB/write; starts Web/CLI | Lazy/help/self-test routing tested; PASS |
| `.env.example` | Non-secret configuration template | Read by operators/tests; no writes/DB/Web | Parse/default/secret tests; PASS |
| `.gitignore` | Excludes secrets, runtime evidence and build/cache state | Git-only | `.env`, `output/`, `git_export/` excluded; PASS |
| `pyproject.toml` | Build, runtime/test dependencies, console script, pytest markers | Build/test tooling | Dependencies valid; version `0.3.0` is P2 |
| `requirements.txt` | Flat runtime/test dependency install option | Package installer | Consistent with used libraries; PASS |
| `.github/workflows/test.yml` | Offline Windows CI | Reads checkout; installs deps; compile/import/pytest; no DB | Read-only permissions, no live marker, lazy-root assertions; PASS |
| `config/README.md` | Sensitivity override instructions | Operator-read only | Must not contain secrets; PASS |
| `config/sensitivity_overrides.toml.example` | Exact/pattern classification example | Loaded only when copied/configured | Override precedence and parsing tested; PASS |
| `run_dashboard.bat` | Windows Web launcher | Selects `.venv` Python; no direct DB/write | Exit propagation and no credential text tested; PASS |
| `run_metadata.bat` | Windows metadata launcher | Selects `.venv` Python; invokes metadata mode | Exit propagation and no credential text tested; PASS |
| `README.md` | Install, launch, modes, safety and current readiness | Operator-facing; no code execution | Updated with live P1 hold; PASS as truthful documentation |
| `OPERATOR_RUN_GUIDE.md` | Ordered safe operation and evidence review | Operator-facing | Updated with late-classification hold; PASS |
| `SAFETY_MODEL.md` | SQL/Web/evidence invariants | Operator/developer-facing | Updated with reconciliation gate; PASS |
| `HTML_FEATURE_CHECKLIST.md` | UI acceptance checklist | Test and reviewer input | “Regenerate Reports” corrected; distinguishes UI PASS from freeze; PASS |
| `RUNTIME_OUTPUT_CONTRACT.md` | Runtime folder/file contract | Developer/reporting reference | Matches contract tests; PASS |
| `FULLRUN_MODULARIZATION_AUDIT.md` | Refactor characterization/evidence | Historical developer audit | Supporting evidence; HISTORICAL |
| `V3_FILE_AUDIT.md` | Earlier v3 file audit | Historical review | Predates v3.1 live failure; HISTORICAL |
| `V3_IMPLEMENTATION_REPORT.md` | Earlier v3 implementation/run evidence | Historical review | Prior successful runs are not v3.1 freeze proof; HISTORICAL |
| `V3_1_REMEDIATION_REPORT.md` | Sequential remediation and exact gate log | Appended after numbered prompts | Current source of Prompt 13/14 evidence; PASS |
| `V3_1_FINAL_FILE_AUDIT.md` | This Prompt 15 audit | Documentation-only local write | Self-described; final verdict NOT READY |

## Python implementation file audit

| File | Purpose / callers | Reads, writes, DB or Web exposure | Safety/tests/status |
|---|---|---|---|
| `src/mssql_database_documenter/__init__.py` | Package identity | No I/O/DB/Web | Version `0.3.0`; P2 |
| `src/mssql_database_documenter/__main__.py` | `python -m` bridge to CLI | Dispatch only | CLI tests; PASS |
| `src/mssql_database_documenter/cli.py` | Controlled dry-run, connection and discovery commands | Reads `.env`; live commands call guarded connection; prints sanitized JSON | Action/mode/config/safety tests; PASS |
| `src/mssql_database_documenter/config.py` | Typed env configuration and validation | Reads environment/dotenv; no DB/write; sanitized Web view | Loopback, auth, ceilings, policies tested; PASS |
| `src/mssql_database_documenter/connection.py` | ODBC connection context | Live DB only; rollback/close; no local write | `ApplicationIntent=ReadOnly`, autocommit false, escaped fields; PASS |
| `src/mssql_database_documenter/contracts.py` | Capability/evidence/output contracts | In-memory constants | Contract/completeness tests; PASS |
| `src/mssql_database_documenter/queries.py` | Registered metadata SQL | DB reads when selected; no writes/Web | All registry SQL validated; PASS |
| `src/mssql_database_documenter/programmable_queries.py` | Programmable-object and SQL Agent metadata SQL | DB reads; Agent command internal analysis field | SELECT-only and Agent tests; PASS |
| `src/mssql_database_documenter/safety.py` | Fail-closed SQL parser/cursor proxy | Final DB execution boundary | Forbidden operations and cursor tests; PASS |
| `src/mssql_database_documenter/redaction.py` | Secret/value redaction | In-memory text only | Redaction tests; PASS |
| `src/mssql_database_documenter/runtime.py` | Identifier, CSV/Markdown/runtime helpers | Writes only within active run paths | SQL validation and contract callers; PASS |
| `src/mssql_database_documenter/inventory.py` | Metadata-only run creation and catalogue | Live DB reads; creates one real run; writes sanitized evidence | Laziness, path, manifest, metadata tests; version literal P2 |
| `src/mssql_database_documenter/fullrun.py` | Sequential lifecycle/orchestrator | Live guarded DB reads; creates/finalizes run evidence | Modularization and full-run tests pass; stage order exposes live P1; P1 |
| `src/mssql_database_documenter/mode_policy.py` | Truthful four-mode policies/ceilings | In-memory configuration | Distinct branch/ceiling tests; PASS |
| `src/mssql_database_documenter/evidence_safety.py` | Independent secret/profile/sample audit | Reads run evidence; no DB; returns fail-closed result | Correctly caught live P1; audit/export tests; PASS |
| `src/mssql_database_documenter/path_safety.py` | Contained destination creation | Local path inspection/creation only | Symlink/junction/reparse tests; PASS |
| `src/mssql_database_documenter/git_export.py` | Explicit audited Git-safe copy | Reads manifested output; stages/copies only after audit; no DB/Web direct | Raw samples forbidden, default exclude, contained publication; PASS; no new live export made |
| `src/mssql_database_documenter/report_regeneration.py` | Offline selected-run presentation refresh | Reads canonical evidence; writes versioned contained copy; no DB | Source hashes, escaping, containment tests; PASS |
| `src/mssql_database_documenter/selftest.py` | Explicit offline developer suite | Fixed subprocess; reads tests; verifies no runtime roots | `shell=False`, sanitized, no DB; PASS |
| `src/mssql_database_documenter/analysis/__init__.py` | Analysis contract exports | No I/O | Import/contract tests; PASS |
| `src/mssql_database_documenter/analysis/stages.py` | Classification, data-quality, risk stages | Reads in-memory evidence; writes run CSV/Markdown; no direct DB/Web | Full-run characterization; PASS |
| `src/mssql_database_documenter/metadata/__init__.py` | Metadata public exports | No I/O | Import/completeness tests; PASS |
| `src/mssql_database_documenter/metadata/support.py` | Optional-feature support states | In-memory/query error classification | Completeness tests; PASS |
| `src/mssql_database_documenter/profiling/__init__.py` | Profiling public API | No I/O | Import/profiling tests; PASS |
| `src/mssql_database_documenter/profiling/policy.py` | Type families and masking adapter | In-memory values | Full-run/mode tests; PASS |
| `src/mssql_database_documenter/profiling/sampler.py` | Bounded table/view sample plan and pre-disk masking | Produces guarded SELECT text; sanitizes rows before caller writes | View/large-table/masking tests; PASS |
| `src/mssql_database_documenter/profiling/sensitivity.py` | Legacy/content/override classification and masking | Reads optional override file; no DB/write | Legacy/value/override tests; PASS in isolation |
| `src/mssql_database_documenter/profiling/stages.py` | Profile, sample, sensitivity and exact-count stages | Guarded DB reads; writes profile/sample evidence | Unit branches pass, but final sample classification is not reconciled into earlier profile extrema; P1 |
| `src/mssql_database_documenter/relationships/__init__.py` | Relationship package API | No I/O | Import/modularization tests; PASS |
| `src/mssql_database_documenter/relationships/inference.py` | Identifier normalization | In-memory only | Characterization/full-run tests; PASS |
| `src/mssql_database_documenter/relationships/stages.py` | Declared/inferred/cardinality/orphan stages | Guarded optional DB reads; writes run evidence | Threshold/access/full-run tests; PASS |
| `src/mssql_database_documenter/lineage/__init__.py` | Lineage public API | No I/O | Import/Agent tests; PASS |
| `src/mssql_database_documenter/lineage/static_sql.py` | Static T-SQL reference extraction | Reads definition text only; no execution/write | Lineage tests; PASS |
| `src/mssql_database_documenter/lineage/agent.py` | Static Agent step analysis/sanitization | Reads internal command text; emits safe metadata only | No execution primitives; subsystem/secret tests; PASS |
| `src/mssql_database_documenter/lineage/stages.py` | Programmable, dependency, Agent and external lineage stages | Guarded catalogue reads; writes sanitized evidence | Agent/full-run tests; PASS |
| `src/mssql_database_documenter/reporting/__init__.py` | Reporting contract exports | No I/O | Contract/import tests; PASS |
| `src/mssql_database_documenter/reporting/stages.py` | Reports, docs, diagrams, manifests, acceptance audit | Reads in-memory/run evidence; writes within active run; no DB direct | Reporting/full-run tests; version literal P2; safety audit correctly fails live run |
| `src/mssql_database_documenter/comparison/__init__.py` | Comparison public API and legacy wrapper | Reads manifested runs; explicit exports | Comparison tests; PASS |
| `src/mssql_database_documenter/comparison/normalizers.py` | Stable CSV/text/number normalization | Reads CSV evidence | Comparison/renderer tests; PASS |
| `src/mssql_database_documenter/comparison/loaders.py` | Manifested run loader | Reads contained run files; no DB/write | Browser/comparison tests; PASS |
| `src/mssql_database_documenter/comparison/diff.py` | 2/3-run status, event and definition diffs | In-memory only | Timeline/multi-event tests; PASS |
| `src/mssql_database_documenter/comparison/engine.py` | Category comparison and truthful summaries | Reads manifested evidence via loader; no DB | Summary/category tests; PASS |
| `src/mssql_database_documenter/comparison/exporters.py` | Static escaped JSON/CSV/HTML export | Explicit contained local writes; no DB | Script-free renderer/containment tests; PASS |
| `src/mssql_database_documenter/web/__init__.py` | Web public API | Import only | Web import tests; PASS |
| `src/mssql_database_documenter/web/app.py` | Flask factory/loopback launcher | Reads settings; starts local Web server; no eager run writes | Lazy/host/header tests; PASS |
| `src/mssql_database_documenter/web/security.py` | CSRF/origin/Host/action allowlist | Request boundary | Web security tests; PASS |
| `src/mssql_database_documenter/web/job_manager.py` | One-job state/progress/cancellation | In-memory/threaded jobs; sanitized logs | Job tests; PASS |
| `src/mssql_database_documenter/web/file_browser.py` | Dual-root browser/run registry | Reads configured roots; no creation; Web-exposed | Traversal/symlink tests; PASS |
| `src/mssql_database_documenter/web/renderers.py` | Safe bounded evidence rendering | Reads selected file; no DB/write; Web-exposed | Bleach/large-file/no-loss tests; PASS |
| `src/mssql_database_documenter/web/routes.py` | Page/raw/download routes | Contained file reads; Web-exposed | Browser/route/security tests; PASS |
| `src/mssql_database_documenter/web/api.py` | Predefined jobs, Git export, regeneration APIs | May invoke authorized DB reads or explicit contained writes | CSRF/action/db allowlist/redaction tests; PASS |
| `src/mssql_database_documenter/web/compare_api.py` | In-memory compare/filter/explicit export API | Reads runs; writes only when `export=true`; Web-exposed | Comparison/Web tests; PASS |

## Web asset audit

| File | Purpose/exposure | Reads/writes/DB | Safety/tests/status |
|---|---|---|---|
| `web/templates/base.html` | Shared local UI shell/navigation | Static rendering only | Local scripts/CSP compatible; PASS |
| `web/templates/dashboard.html` | Guided actions/jobs/regeneration | Browser submits predefined APIs | Escaped Jinja, correct offline regeneration wording; PASS |
| `web/templates/browser.html` | Evidence folder browser | Browser query parameters only | Server containment is authoritative; PASS |
| `web/templates/file_view.html` | Formatted/raw evidence view guidance | Displays sanitized renderer output | Executable HTML removed; PASS |
| `web/templates/compare.html` | 2/3-run controls and result tables | Browser state/API calls | Exact/multi-event filters tested; PASS |
| `web/templates/run_detail.html` | Manifest/status/mode/safety details | Displays registry metadata | Explicit audit-first guidance; PASS |
| `web/templates/help.html` | Layperson workflow/safety/help | Static operator guidance | Updated to warn failed local audit may retain unsafe diagnostic evidence; PASS |
| `web/templates/error.html` | Generic sanitized error page | No privileged action | No exception detail leakage; PASS |
| `web/static/js/dashboard.js` | CSRF jobs, polling, cancellation, regeneration/export controls | Calls only fixed API routes | Full-readonly confirmation and error handling tested through Web suite; PASS |
| `web/static/js/browser.js` | Browser table interaction | DOM only | No server authority; PASS |
| `web/static/js/compare.js` | 2/3-run selection/filter/pagination | Calls compare APIs | Timeline event filter tests; PASS |
| `web/static/css/app.css` | Responsive shared styling | Presentation only | No safety effect; Web/mobile evidence; PASS |
| `web/static/css/details.css` | Evidence/detail styling | Presentation only | No safety effect; PASS |

All Web asset paths above are relative to
`src/mssql_database_documenter/`.

## Test file audit

| File | Responsibility | I/O/DB boundary | Result/status |
|---|---|---|---|
| `tests/test_agent_lineage.py` | Agent static parsing, sanitization, edges, no execution | Fixtures only; no DB | PASS |
| `tests/test_ci_quality_gate.py` | Workflow content/offline constraints | Reads CI YAML | PASS |
| `tests/test_cli.py` | Dry-run laziness | Mock/no DB | PASS |
| `tests/test_comparison.py` | 2/3-run timelines, summaries, filters, static export | Temporary files only | PASS |
| `tests/test_config.py` | Env/auth/mode/ceiling/default validation | Temporary/env only | PASS |
| `tests/test_connection.py` | Connection-string read-only intent/escaping | No live connection | PASS |
| `tests/test_evidence_safety.py` | Profile/sample/secret audit and export rejection | Temporary evidence | PASS; includes exact earlier-unknown/final-sensitive rejection but not reconciliation repair |
| `tests/test_file_browser.py` | Lazy roots, traversal/symlink, registry/export | Temporary files | PASS |
| `tests/test_fullrun.py` | SQL, contracts, masking, lifecycle, sequential databases | Mocks/temporary files | PASS; extrema test covers classification known before persistence, not late upgrade |
| `tests/test_fullrun_characterization.py` | Refactor behavior lock | In-memory/temp | PASS |
| `tests/test_fullrun_modularization.py` | Ownership/import/orchestrator size | Source inspection | PASS |
| `tests/test_git_export_policy.py` | Exclude/masked-only/raw rejection | Temporary files | PASS |
| `tests/test_inventory.py` | Metadata run path/contracts/manifests | Mocks/temp | PASS |
| `tests/test_job_manager.py` | State, lock, cancellation, redaction | In-memory | PASS |
| `tests/test_metadata_completeness.py` | Families/support/artifacts/security hashing | Mocks/temp | PASS |
| `tests/test_mode_policy.py` | Four distinct policies and ceilings | In-memory/temp | PASS |
| `tests/test_path_containment.py` | Real Windows junction/reparse publication attacks | Temporary junctions | PASS, no privilege skip in prior focused run |
| `tests/test_redaction.py` | Secrets and escaped-server redaction | In-memory | PASS |
| `tests/test_renderers.py` | Safe/no-loss/large-file renderers | Temporary files | PASS |
| `tests/test_report_regeneration.py` | Offline/source-preserving/static regeneration | Temporary runs | PASS |
| `tests/test_runtime_self_test.py` | No runtime pytest; explicit fixed self-test | Mocked subprocess/temp | PASS |
| `tests/test_safety.py` | SQL grammar and cursor boundary | Mock cursor | PASS |
| `tests/test_sampler.py` | View/large-table plans, status, pre-disk masking | Mocks/temp | PASS |
| `tests/test_sensitivity.py` | Legacy names, overrides, content signals | In-memory/temp config | PASS |
| `tests/test_web_app.py` | Launcher/lazy/Web security/actions/browser/compare/export/regeneration | Flask test client/temp; DB mocked | PASS |

Latest Prompt 15 offline run:

`157 passed, 2 skipped, 241 subtests passed in 8.00s`

Compile gate also passed. The two skips are existing platform/availability skips, not
test failures.

## Prompt/specification document audit

The 72 files in `Prompts/` are immutable requirement, sequencing, audit-reference,
manifest, checksum, environment-example, and handoff documents. They are read by
operators/implementers only; they perform no local writes, DB access, or Web exposure.

| Scope | Files individually covered | Integrity/status |
|---|---|---|
| `Prompts/MSSQL_DB_Documentation_Prompt/` | `00_README.md`, numbered `01` through `21`, `PACK_MANIFEST.json`, `PACK_CHECKSUMS.sha256` | 24 files; all 23 checksum entries match; PASS/HISTORICAL specification |
| `Prompts/SchoolERP_MSSQL_Documenter_v3_WebUI_Prompt_Pack/` | `00_FINE_COMB_AUDIT_FINDINGS.md`, `00_START_HERE.md`, numbered `01` through `21`, `PACK_MANIFEST.json`, `PACK_CHECKSUMS.sha256` | 25 files; all 24 checksum entries match; PASS/HISTORICAL specification |
| `Prompts/SchoolERP_MSSQL_Documenter_v3_1_Remediation_Prompt_Pack/` | `00_START_HERE.md`, numbered `01` through `15`, `ACCEPTANCE_MATRIX.md`, `IMPLEMENTATION_HANDOFF_TEMPLATE.md`, `SOURCE_AUDIT_REFERENCE.md`, `PACK_MANIFEST.json`, `PACK_CHECKSUMS.sha256` | 21 files; all 20 checksum entries match; PASS/current specification |
| Standalone prompt docs | `REPAIR_AND_LAYMAN_UI_IMPLEMENTATION_PLAN.md`, `V3_PROMPT_PACK_SEQUENTIAL_EXECUTION_2026-09-05.md` | 2 files; historical plan/execution evidence |

No prompt/specification file was modified by Prompt 15.

## v3.1 acceptance matrix disposition

| IDs | Disposition | Evidence |
|---|---|---|
| A01-A04 | PASS | Canonical main, lazy lifecycle, guarded read-only SQL, no arbitrary Web action |
| A05-A07 | PASS with live defect outside exporter | Legacy/content/override classification and fail-closed Git policies work; local profile reconciliation P1 still blocks run acceptance/export |
| A08-A09 | PASS | DB1 attempted two views; large-table sampling policy is independent, though DB1 had no table over threshold |
| A10-A27 | PASS offline | Modes, Agent, metadata, modularization, self-test, comparison, reports, CI, containment, evidence audit, docs and offline suite verified |
| A28 | **FAIL** | DB1 safe-profile run `20260906_150848` failed final masking audit |
| A29 | BLOCKED | DB2 prohibited until DB1 passes |
| A30 | BLOCKED | Three-run live smoke prohibited/not performed after DB1 failure |
| A31 | PASS | This fine-comb audit was produced |

## Live evidence disposition

| Run/gate | Status | Sharing/export disposition |
|---|---|---|
| DB1 dry-run | PASS; 35 queries; no connection | No evidence root created |
| DB1 connection test | PASS; 3 guarded result sets | No run created |
| `20260906_150548` metadata | COMPLETED; 20/20; 0 errors/warnings; audit PASS | Local validated metadata evidence; no Git export requested |
| `20260906_150721` metadata+logic | COMPLETED; 20/20; 0 errors/warnings; audit PASS | Local validated logic evidence; no Git export requested |
| `20260906_150848` safe-profile | FAILED; 15/20; one PII profile violation | Local diagnostic only; do not share/export |
| DB2 | Not run | Blocked by DB1 gate |
| Three-run comparison | Not run | Blocked by DB1 gate |
| Full-readonly | Not run | Not separately authorized |

Zero Git-export paths match the three new run IDs.

## Required-document disposition

- `V3_1_REMEDIATION_REPORT.md`: present and updated through Prompt 14.
- `V3_1_FINAL_FILE_AUDIT.md`: created by Prompt 15.
- `README.md`: updated with the current live-validation hold.
- `OPERATOR_RUN_GUIDE.md`: updated with the safe stop rule.
- `SAFETY_MODEL.md`: updated with final-classification reconciliation behavior.
- `web/templates/help.html`: updated with failed-audit handling for lay users.
- `HTML_FEATURE_CHECKLIST.md`: corrected to offline Regenerate Reports and scoped
  its PASS to UI features rather than product freeze.

## Final gate declaration

- P0 unresolved: none identified.
- P1 unresolved: **one - late sensitivity classification/profile masking reconciliation**.
- P2 unresolved or unaccepted: **one - v3.1 release identity/versioning**.
- Offline gates: PASS.
- Authorized live gates: FAIL at DB1 safe-profile.
- DB2/live comparison: correctly BLOCKED and not performed.
- Git export of new live evidence: not performed.
- Freeze action: not performed.

Final Prompt 15 disposition: **AUDIT COMPLETE; v3.1 FREEZE DENIED**.

Next permitted work is a focused remediation of the P1 reconciliation defect and
the P2 release identity, followed by Prompt 13 and Prompt 14 reruns in order. Do not
edit the failed canonical evidence into a passing state.

## 2026-09-07 post-audit remediation addendum

The original audit and failed live evidence above are retained unchanged as historical
truth. The two source findings and the documentation/execution-record gaps have since
been repaired:

| Finding | Current disposition | Evidence |
|---|---|---|
| P1 late sensitivity/profile reconciliation | REMEDIATED OFFLINE | Final classification is reconciled into profile and low-cardinality rows and values are re-masked; Unknown-to-PII regression passes; full suite passes |
| P2 release identity | REMEDIATED | One `0.3.1` package identity feeds inventory/reporting; project/package consistency test passes; no production `0.3.0` literal remains |
| Stale runtime/config/implementation documentation | REMEDIATED | Runtime regeneration/export/sensitivity contract expanded; local override procedure and precedence documented; current status added to README, operator guide, safety model, checklist, Web-aligned implementation report |
| Missing dedicated Prompt 11/12 report sections | REMEDIATED | Fresh sequential focused gates and exact results appended to `V3_1_REMEDIATION_REPORT.md` with an explicit reconstruction label |
| Prompt 13 rerun | PASS | Compile/import/help/self-test/dry-run/full and focused suites/static review/laziness fingerprints all pass |

Current complete suite evidence is **159 passed, 2 skipped, 241 subtests**. The two
skips remain environment-dependent Windows symlink-creation cases; real junction
containment regressions pass.

The project `.venv` is healthy on Python 3.13.14: `pip check` reports no broken
requirements, package source and installed distribution metadata both report `0.3.1`,
and the installed console entry point responds successfully.

Current gate declaration:

- unresolved offline P0: none;
- unresolved source P1: none;
- unresolved P2: none;
- failed run `20260906_150848`: unchanged, local-only, and ineligible for export;
- fresh DB1 live revalidation: pending explicit authorization;
- DB2, live three-run smoke, Git export of new live evidence, and full-readonly: not
  performed after this repair.

Therefore the source/offline blockers are repaired, but **v3.1 is not yet declared
ready to freeze**. Prompt 14 must restart at DB1 dry-run and proceed sequentially only
after each live gate passes.

## 2026-09-07 Prompt 14 live-validation addendum

Prompt 14 was explicitly authorized after the offline repair and completed
sequentially for both configured databases. Exact run, audit, checksum, export, sample,
Agent, metadata, warning, and comparison evidence is recorded in
`V3_1_REMEDIATION_REPORT.md`.

- DB1 safe-profile `20260907_015218`: 20/20 stages, audit PASS, independent re-audit
  PASS, former failing PII profile extrema masked, one broken-view warning.
- DB2 safe-profile `20260907_015839`: 20/20 stages, audit PASS, independent re-audit
  PASS, one broken-view warning.
- both explicit Git exports: `exclude` policy, zero sample payload CSVs, zero configured
  identity/credential hits, independent audit and checksums PASS;
- DB1 A/B/C production comparison: PASS with the expected mixed-mode warning, two
  multi-event rows, static script-free export, and HTTP 200 local safe-renderer route;
- full-readonly was not separately authorized and was not run;
- failed historical run `20260906_150848` remains unchanged and ineligible for export.

This addendum closes the prior live-validation blocker but does not replace or silently
rewrite the historical Prompt 15 verdict. A fresh Prompt 15 fine-comb review is still
required before any `READY TO FREEZE` declaration.

## 2026-09-07 Prompt 15 final fine-comb rerun

Status: **PASS**

The previous exhaustive purpose/caller/read/write/DB/Web/safety/test/status matrices
were revalidated against the current tree rather than discarded. Current inventory is
183 project-owned files with no generated runtime or environment state included:

| Class | Files | Audit result |
|---|---:|---|
| Production Python | 52 | PASS |
| Web templates/static assets | 13 | PASS |
| Tests | 25 | PASS |
| Configuration/packaging/CI | 7 | PASS |
| Root launchers, reports, audits, and documentation | 14 | PASS |
| Prompt/specification pack files | 72 | PASS |
| **Total** | **183** | **PASS** |

The one-file increase from the original 182-file audit is durable audit/report state
created during remediation; no egg-info, cache, bytecode, output, Git export,
virtual-environment, or `.env` file was misclassified as project source. All 20 entries
in `PACK_CHECKSUMS.sha256` independently match.

### Named regression disposition

| Search area | Final result |
|---|---|
| Eager directory creation / startup output or export | PASS: import, `create_app`, help, self-test, dry-run, and in-memory comparison remain lazy; exact runtime fingerprints unchanged |
| Arbitrary SQL / unguarded cursor | PASS: 35 registered queries validate SELECT-only; every execution path reaches `ReadOnlyCursor`; `executemany` denied |
| Discovered-code or SQL Agent execution | PASS: stored definitions and Agent commands are static text inputs only; persisted Agent evidence has no raw command field |
| Shell / unsafe subprocess | PASS: no `os.system`, production `eval`/`exec`, `Popen`, or `shell=True`; only fixed-argv explicit self-test uses subprocess |
| Secrets / raw samples | PASS: configured-value scan found zero project-source hits; evidence/export audits pass; raw Git-export sample mode does not exist |
| Misleading report action | PASS: selected-run regeneration is offline, versioned, contained, source-hash guarded, and DB-independent |
| Script-dependent comparison HTML | PASS: exported report source has zero scripts and remains readable after all surrounding UI scripts are removed |
| Safe/full mode aliasing | PASS: independently resolved policies and hard ceilings; full mode must be materially deeper |
| Monolithic leftovers | PASS with accepted maintainability note: 364-line `fullrun.py` owns lifecycle/orchestration; cohesive domain registries/stages remain separate |
| Runtime pytest coupling | PASS: discovery runtime never invokes pytest; only explicit self-test/CI does |
| Missing MSSQL metadata contracts | PASS: query, feature-state, artifact, capability, comparison, and tests cover all required families |
| Two-run assumptions / three-run filter gaps | PASS: exactly 2/3 runs, A-B/B-C/A-C intervals, multi-event filters, totals, exports, and Web API are covered |
| Missing CI | PASS: Windows/Python 3.11 workflow compiles/imports/tests offline and rejects runtime-root creation without secrets/live DB |
| Publication/path containment | PASS: shared guard and junction/symlink regressions cover Git, comparison, regeneration, and file browsing |
| Late sensitivity reconciliation | PASS: strongest final category is reconciled and earlier profile/low-cardinality values are re-masked; unit and live DB1 proof pass |
| Release identity | PASS: project, package, installed distribution, inventory, and reporting use `0.3.1` |

### Final offline evidence

- Python 3.13.14; project requirement Python 3.11+;
- `pip check`: no broken requirements;
- compile/import/application factory/version agreement: PASS;
- launcher help and 35-query non-connecting dry-run: PASS;
- explicit self-test: **159 passed, 2 skipped, 241 subtests**;
- independent full offline suite: **159 passed, 2 skipped, 241 subtests**;
- two skips are Windows symlink-creation permission cases; real junction containment
  tests pass;
- output and Git-export inventory fingerprints remained unchanged.

### Final live evidence

- DB1 runs: metadata `20260907_014959`, metadata+logic `20260907_015059`,
  safe-profile `20260907_015218`;
- DB2 runs: metadata `20260907_015651`, metadata+logic `20260907_015735`,
  safe-profile `20260907_015839`;
- both safe-profile runs: 20/20 stages, zero errors, generated and independent audits
  PASS with zero violations, all checksums valid;
- each safe-profile run has one accepted object-level warning for the existing broken
  `dbo.feespegv` view; the affected sample is explicitly unavailable and other stages
  remain valid;
- DB1 former P1 identity is final PII/PSEUDONYMIZE/HIGH with masked extrema;
- both explicit Git exports use `exclude`, contain zero sample payload CSVs and zero
  configured identity/credential hits, and pass audit/checksum validation;
- three-run comparison: 44 categories, 13,147 rows, all status filters exercised, two
  multi-event rows, static script-free HTML/CSV/JSON, local route HTTP 200 and readable
  after script removal;
- interactive visual browser control was unavailable and is not claimed; the actual
  local renderer route and script-independent presentation contract passed;
- full-readonly was not separately authorized in Prompt 14 and was not rerun.

### Final severity and freeze gate

- unresolved P0: **0**;
- unresolved P1: **0**;
- unresolved P2: **0**;
- offline gates: **PASS**;
- authorized live gates: **PASS WITH TWO DOCUMENTED OBJECT-LEVEL VIEW WARNINGS**;
- required documentation: **PASS**;
- historical failed evidence: preserved, local-only, and excluded from export/compare;
- source commit/tag/release/deployment action: not requested and not performed.

**MSSQL DOCUMENTATION TOOL v3.1 — READY TO FREEZE**
