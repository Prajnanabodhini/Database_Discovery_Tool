# MSSQL Database Discovery Tool v3.1 Remediation Report

> **Historical v3.1 remediation record.** Retained for provenance and
> superseded as current release authority by `V3_1_1_HARDENING_REPORT.md`.

## Baseline and guardrails - Prompt 02

Status: **PASS - baseline frozen; no remediation code changed**  
Recorded: 2026-09-06  
Repository: `Prajnanabodhini/Database_Discovery_Tool`

### Starting repository state

| Evidence | Result |
|---|---|
| Branch | `main` |
| Starting HEAD | `1c608d12d7c0f107931144dbbdc4e536865ab546` |
| Audited/frozen SHA | `1c608d12d7c0f107931144dbbdc4e536865ab546` |
| HEAD comparison required | No; HEAD exactly matches the audited SHA |
| Pre-existing working-tree state | `?? Prompts/SchoolERP_MSSQL_Documenter_v3_1_Remediation_Prompt_Pack/` |
| Tracked `output/` files | None |
| Tracked `git_export/` files | None |
| Historical runtime evidence | Preserved without deletion, rewriting, export, or regeneration |

The untracked v3.1 prompt pack is operator-provided work and must be preserved. No
reset, clean, checkout, history rewrite, or destructive command was used.

### Python and tool baseline

| Tool/package | Version or state |
|---|---|
| Project package | `mssql-database-documenter 0.3.0` |
| Available system Python used for offline gate | Python `3.11.9` |
| pip | `24.0` |
| Git | `2.55.0.windows.5` |
| Flask | `3.1.3` |
| pyodbc package metadata | `5.3.0` |
| Markdown | `3.10.3` |
| bleach | `6.4.0` |
| pytest | `9.1.1` |

Environment finding: the existing `.venv` was created at the former project path and
its `pyvenv.cfg` points to an inaccessible Microsoft Store Python 3.13 installation.
Consequently `.venv\Scripts\python.exe` cannot currently start. The baseline did not
repair or reinstall it. Offline verification used the available Python 3.11 with
`PYTHONPATH` limited to the current project source and the existing venv package
directory. Bytecode and pytest cache creation were disabled.

### Preserved v3 implementation inspected

The baseline inspection covered:

- canonical `main.py` and both Windows launchers;
- typed environment configuration and sanitized diagnostics;
- ODBC connection construction, timeout, read-only intent, rollback and close;
- fail-closed SQL validator and `ReadOnlyCursor` execution boundary;
- registered metadata and programmable-object query catalogues;
- sequential discovery orchestration in `fullrun.py`;
- independent evidence audit and explicit Git exporter;
- comparison loaders, normalizers, diff engine and exporters;
- Flask application, security hooks, job manager, file browser, renderers, routes,
  APIs, templates and static clients;
- existing offline tests and runtime/output contracts.

This was an inspection and characterization pass only. The known v3.1 findings remain
unfixed at this gate, including legacy PII classification, sample coverage, mode
semantics, SQL Agent lineage, metadata breadth, monolithic orchestration, runtime
pytest coupling, comparison export/filter/totals, reports-action semantics and CI.

### Offline and lazy checks

| Check | Result | Evidence |
|---|---|---|
| Source/package imports | PASS | Exit code 0 |
| Root `main.py --help` | PASS | Exit code 0; expected launcher description present |
| Flask application factory | PASS | Exit code 0; 22 routes constructed; no server or DB connection started |
| Registered-query dry run | PASS | Exit code 0; 21 queries validated; `connection_attempted=false` |
| Current offline test suite | PASS | `86 passed, 2 skipped, 89 subtests passed` |
| Runtime evidence laziness | PASS | Evidence fingerprint unchanged before/after all checks |

The two skipped tests are the existing Windows symlink-creation cases that skip when
the current identity lacks the operating-system privilege. Other containment and
traversal tests passed.

Historical evidence fingerprint:

| Measurement | Before | After |
|---|---:|---:|
| Files across `output/` and `git_export/` | 4,622 | 4,622 |
| Total bytes | 55,095,186 | 55,095,186 |
| Path/length/timestamp metadata SHA-256 | `0a454797d3c98b66ff56c29f598bff17b6023977a38b44b41a6ee81f9e68a4c1` | `0a454797d3c98b66ff56c29f598bff17b6023977a38b44b41a6ee81f9e68a4c1` |

Therefore import, help, application construction, dry-run and tests created no run,
created no Git export, and did not mutate historical evidence.

### Guardrail searches

| Search/control | Result |
|---|---|
| Production `shell=True` | None |
| Production `os.system(...)` | None |
| Production `eval(...)` | None |
| Production runtime `exec(...)` | None |
| Arbitrary SQL/shell Web endpoint | None found; Web actions use a closed allowlist |
| Direct execution boundary | All application query paths use `ReadOnlyCursor`; its raw cursor call follows immediate `validate_read_only_sql` validation |
| Registered SQL safety | PASS through the 21-query offline dry run; registered statements are SELECT-based |
| Tracked credential/runtime candidates | Only the non-secret `.env.example`; no `.env`, credential file, runtime output, Git export, key or log is tracked |
| Production subprocess | One fixed-argument `python -m pytest -q` call in `fullrun.py` stage 21; this is a known v3.1 remediation item, not arbitrary user-controlled execution |

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Runtime discovery evidence created: **No**.
- Git export created: **No**.
- Historical output/export changed: **No**.
- Production source code changed: **No**.
- Only deliverable written: this baseline section/report.

Prompt 02 is complete. Prompt 03 has not been read or executed in this gate and
requires a separate operator continuation.

## PII and Git export hardening - Prompt 03

Status: **PASS - implementation, focused tests, and full offline regression gate complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Implemented design

- Extracted sensitivity classification and masking into
  `profiling/sensitivity.py`.
- Classification now returns category, masking action, confidence, and evidence.
- Implemented deterministic precedence: exact operator overrides, pattern operator
  overrides, built-in legacy/modern column heuristics, extended-property heuristics,
  value-pattern signals, and finally `Unknown`.
- Added legacy School ERP recognition including `StudNm`, `FName`, `MName`,
  `FatherNm`, `MobNo`, `PhNo`, `ContactNo`, `Addr1`, `ResAdd`, `BDate`, and
  `BirthDt`.
- Added `config/sensitivity_overrides.toml.example` and the
  `SENSITIVITY_OVERRIDES_FILE` configuration key.
- Integrated the centralized classifier into profiling, sampling, the sensitivity
  catalogue, masking reports, and the independent evidence audit.
- Strengthened the audit so final catalogue sensitivity cannot be weakened by an
  earlier `Unknown` profile-row label, and so every sample payload is independently
  inspected even if its masking report omits a sensitive column.

### Git export policy

| Requirement | Result |
|---|---|
| Configuration | `GIT_EXPORT_SAMPLE_POLICY=exclude|masked_only` |
| Default | `exclude` |
| Raw mode | Not implemented; any other value fails configuration/export validation |
| `exclude` | Sample payload CSVs omitted; `SAMPLE_INDEX.csv` and `MASKING_REPORT.csv` retained |
| `masked_only` | Every non-empty payload cell is masked/redacted in a temporary staged copy |
| Source mutation | None; source sample SHA-256 is asserted unchanged |
| Policy evidence | Written to export manifest, checklist, and `GIT_EXPORT_POLICY.json` |
| Publication boundary | Staged candidate is independently audited; destination is created only after PASS |
| Checksums | Export manifest inventory and SHA-256 catalogue are regenerated for staged contents |
| Web integration | Explicit Git-export action passes the configured policy |

The staged-copy design means an audit or copy failure does not leave a partial
published Git-export run. Credential categories use `[REDACTED]`; all other staged
sample values use deterministic `[MASKED:<16 hex>]` tokens. The original run is not
rewritten.

### Files changed for this gate

- `.env.example`
- `config/sensitivity_overrides.toml.example`
- `src/mssql_database_documenter/config.py`
- `src/mssql_database_documenter/profiling/__init__.py`
- `src/mssql_database_documenter/profiling/sensitivity.py`
- `src/mssql_database_documenter/fullrun.py`
- `src/mssql_database_documenter/evidence_safety.py`
- `src/mssql_database_documenter/git_export.py`
- `src/mssql_database_documenter/web/api.py`
- `tests/test_config.py`
- `tests/test_evidence_safety.py`
- `tests/test_sensitivity.py`
- `tests/test_git_export_policy.py`

### Verification evidence

| Gate | Result |
|---|---|
| Changed Python modules compile | PASS |
| Focused privacy/export/config/browser suite | `27 passed, 2 skipped, 16 subtests passed` |
| Full offline regression suite | `94 passed, 2 skipped, 102 subtests passed` |
| Legacy-name recognition | PASS for all required examples |
| Exact override beats pattern and built-in | PASS |
| Raw sensitive profile evidence rejected | PASS |
| Final catalogue catches earlier unknown raw profile | PASS |
| Default payload exclusion/control retention | PASS |
| Masked-only full-text no-leakage check | PASS |
| Original sample SHA-256 unchanged | PASS |
| Regenerated export checksums validate | PASS |
| Invalid/raw sample policy rejected without destination | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

The two skips remain the pre-existing Windows symbolic-link privilege cases.

Historical evidence remained at **4,622 files / 55,095,186 bytes**, exactly matching
the Prompt 02 baseline after both Prompt 03 test gates. Tests used temporary
directories only.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real Git export created: **No**.
- Prompt 03 acceptance requirements: **PASS**.

Prompt 03 is complete. Per the sequential stop rule, Prompt 04 has not been read or
started and requires a separate operator continuation.

## View and large-table sample coverage - Prompt 04

Status: **PASS - implementation, focused tests, and full offline regression gate complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Implemented design

- Added the dedicated `profiling/sampler.py` module for sample eligibility, bounded
  SQL planning, indexed ordering selection, failure classification, sensitivity
  classification, and pre-persistence masking.
- Kept deep-profile eligibility separate: `prompt07_profile` still fails closed when
  a table estimate exceeds `PROFILE_LARGE_TABLE_THRESHOLD` or is unavailable.
- Table sampling now attempts bounded `TOP (N)` reads independently of the deep
  profile threshold when `SAMPLE_LARGE_TABLES=true`.
- Table ordering uses primary-key columns first, then an enabled/unfiltered unique
  index. When neither exists it uses unordered `TOP (N)` rather than sorting an
  arbitrary column.
- View sampling does not consult table-size metadata and uses bounded unordered
  `TOP (N)` reads.
- Sampling never performs an exact row count and does not use random ordering or
  `TABLESAMPLE`.
- Existing connection/cursor query timeouts apply to every sample query. Timeout,
  access, other query failure, empty result, disabled, and successful states are
  represented explicitly without turning one inaccessible view into a stage-wide
  failure.
- Sensitive sample columns are always masked by the sampler before rows are returned
  to the CSV writer, including when the legacy profile-masking flag is false.

### Normalized settings and compatibility

| Canonical setting | Default | Behavior |
|---|---:|---|
| `SAMPLE_TABLES` | `true` | Enables bounded table samples |
| `SAMPLE_VIEWS` | `true` | Enables bounded view samples |
| `SAMPLE_LARGE_TABLES` | `true` | Allows bounded samples above the deep-profile threshold |
| `SAMPLE_ROW_LIMIT` | `100` | Positive integer used directly in `TOP (N)` |

`PROFILE_INCLUDE_SAMPLE_DATA` and `PROFILE_SAMPLE_ROWS` remain accepted as fallbacks
when their canonical replacements are absent. When canonical variables are present,
they take precedence. Sanitized configuration, run summaries, inventory summaries,
comparison loading, and the dashboard now expose/use the canonical values while
retaining legacy fields for older run compatibility.

### Sample index contract

`SAMPLE_INDEX.csv` now records:

- schema and object name;
- object type;
- requested and returned row counts;
- ordering strategy;
- explicit status;
- masked-sensitive-column count.

Sample payloads remain header-only for disabled, inaccessible, timed-out, failed, or
empty objects, while the index states why no rows were retained.

### Files changed for this gate

- `.env.example`
- `src/mssql_database_documenter/config.py`
- `src/mssql_database_documenter/profiling/__init__.py`
- `src/mssql_database_documenter/profiling/sampler.py`
- `src/mssql_database_documenter/fullrun.py`
- `src/mssql_database_documenter/inventory.py`
- `src/mssql_database_documenter/comparison/loaders.py`
- `src/mssql_database_documenter/web/templates/dashboard.html`
- `tests/test_config.py`
- `tests/test_sampler.py`

### Verification evidence

| Gate | Result |
|---|---|
| Changed Python modules compile | PASS |
| Focused sampler/config/full-run/privacy suite | `49 passed, 63 subtests passed` |
| Full offline regression suite | `105 passed, 2 skipped, 102 subtests passed` |
| View with no table-size estimate is sampled | PASS |
| Large table above profile threshold is sampled | PASS |
| Same large table remains excluded from deep profile | PASS |
| Generated sample SQL passes fail-closed validator | PASS |
| Sample SQL contains no exact count | PASS |
| Sampler source contains no `ORDER BY NEWID` or `TABLESAMPLE` | PASS |
| PK/unique-only ordering selection | PASS |
| Timeout recorded as `FAILED_TIMEOUT` in sample index | PASS |
| Sensitive table/view values absent from persisted CSV text | PASS |
| Masking enforced despite legacy profile-masking flag being false | PASS |
| Canonical settings override legacy aliases | PASS |
| Legacy-only settings still map to canonical behavior | PASS |
| Non-positive sample limit rejected | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

The two skips remain the pre-existing Windows symbolic-link privilege cases.

Historical evidence remained at **4,622 files / 55,095,186 bytes**, exactly matching
the Prompt 02 baseline after both Prompt 04 test gates. All sampling tests used
temporary synthetic evidence only.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 04 acceptance requirements: **PASS**.

Prompt 04 is complete. Per the sequential stop rule, Prompt 05 has not been read or
started and requires a separate operator continuation.

## Discovery mode semantics - Prompt 05

Status: **PASS - implementation, focused tests, and full offline regression gate complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Resolved policy architecture

Added immutable `ResolvedModePolicy` resolution in
`src/mssql_database_documenter/mode_policy.py`. The orchestrator no longer derives
mode behavior from scattered `logic_enabled` or `profile_enabled` booleans. Exact
counts, profiles, samples, relationship validation, programmable logic, pipeline
metadata, low-cardinality depth, and extended validation all use the one policy
resolved before a run directory is created.

| Mode | Programmable logic/pipelines | Table/view data scans | Effective behavior |
|---|---|---|---|
| `metadata` | No | No | Structural catalog and size/shape metadata only |
| `metadata+logic` | Yes | No | Adds definitions, static dependencies, external references, and pipeline metadata |
| `safe-profile` | Yes | Yes | Conservative profiles, bounded samples, sensitivity and relationship validation; exact counts forced off |
| `full-readonly` | Yes | Yes | Separate larger limits, extended distribution validation, deeper relationships, and optional ceiling-controlled exact counts |

`metadata` and `metadata+logic` resolve profile, sample, exact-count, relationship,
and low-cardinality limits to zero. Even if `PROFILE_EXACT_ROW_COUNTS=true`, neither
metadata mode can execute the dynamic `COUNT_BIG` branch.

### Full Read-Only configuration and hard ceilings

Added:

- `FULL_READONLY_SAMPLE_ROW_LIMIT` (default 500; ceiling 2,000);
- `FULL_READONLY_PROFILE_THRESHOLD` (default 5,000,000; ceiling 10,000,000);
- `FULL_READONLY_EXACT_COUNT_THRESHOLD` (default 500,000; ceiling 1,000,000);
- `FULL_READONLY_RELATIONSHIP_THRESHOLD` (default 5,000,000; ceiling 10,000,000);
- `FULL_READONLY_LOW_CARDINALITY_LIMIT` (default 200; ceiling 1,000);
- `FULL_READONLY_EXTENDED_VALIDATION` (default true).

Safe Profile retains separate ceilings of 500 sample rows, 1,000,000 profile and
relationship rows, and 100 low-cardinality values. Full Read-Only limits cannot
resolve below their Safe Profile counterparts, and a configuration with no genuinely
deeper effective branch is rejected. Optional exact counts require both Full
Read-Only mode and `PROFILE_EXACT_ROW_COUNTS=true`.

Policy violations fail before `_new_run_directory`, preventing invalid configuration
from creating misleading partial evidence.

### Persisted policy evidence

The complete resolved policy, including `permits_data_scans`, is persisted in:

- `00_Run_Metadata/RUN_CONFIGURATION.json`;
- `00_Run_Metadata/run_summary.json`;
- `00_Run_Metadata/manifest.json` both as a top-level record and inside sanitized
  configuration.

The metadata-only inventory runner explicitly records its effective mode as
`metadata`, while retaining the ambient requested mode separately. Dry-run output
also exposes the resolved policy without connecting. Run-detail UI presents policy
branches and effective thresholds when available; older runs remain loadable.

### Operator and UI guidance

Updated `.env.example`, `README.md`, `OPERATOR_RUN_GUIDE.md`, dashboard action/help
text, the full Help page, and run details. The guidance now states that metadata modes
perform no table/view data scans, Safe Profile never performs exact counts, and Full
Read-Only requires separate approval because its larger bounded limits can consume
more resources.

### Files changed for this gate

- `.env.example`
- `README.md`
- `OPERATOR_RUN_GUIDE.md`
- `src/mssql_database_documenter/mode_policy.py`
- `src/mssql_database_documenter/config.py`
- `src/mssql_database_documenter/fullrun.py`
- `src/mssql_database_documenter/inventory.py`
- `src/mssql_database_documenter/cli.py`
- `src/mssql_database_documenter/comparison/loaders.py`
- `src/mssql_database_documenter/web/api.py`
- `src/mssql_database_documenter/web/templates/dashboard.html`
- `src/mssql_database_documenter/web/templates/help.html`
- `src/mssql_database_documenter/web/templates/run_detail.html`
- `tests/test_mode_policy.py`
- `tests/test_config.py`
- `tests/test_fullrun.py`
- `tests/test_inventory.py`
- `tests/test_sampler.py`
- `tests/test_web_app.py`

### Verification evidence

| Gate | Result |
|---|---|
| Changed Python modules compile | PASS |
| Focused policy/runtime/config/CLI/UI suite | `67 passed, 73 subtests passed` |
| Full offline regression suite | `113 passed, 2 skipped, 104 subtests passed` |
| Four resolved policies structurally distinct | PASS |
| Metadata exact-count request executes zero dynamic scans | PASS for both metadata modes |
| Safe Profile exact-count request remains disabled | PASS |
| Full Read-Only exact-count request executes only below resolved ceiling | PASS |
| Two-million-row synthetic table skipped by Safe Profile | PASS |
| Same table profiled with deeper Full Read-Only defaults | PASS |
| Full Read-Only performs deeper low-cardinality branch | PASS |
| Hard-ceiling violation rejected before output-root creation | PASS |
| Shallower/indistinct Full Read-Only policy rejected | PASS |
| Policy present in run config, summary, and manifest | PASS |
| Standalone inventory records metadata/no-scan policy | PASS |
| UI/help/operator guide describes actual mode boundaries | PASS |
| No scattered legacy mode booleans remain in orchestrator | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

The two skips remain the pre-existing Windows symbolic-link privilege cases.

Historical evidence remained at **4,622 files / 55,095,186 bytes**, exactly matching
the Prompt 02 baseline after both Prompt 05 test gates. All branch and persistence
tests used temporary synthetic evidence only.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 05 acceptance requirements: **PASS**.

Prompt 05 is complete. Per the sequential stop rule, Prompt 06 has not been read or
started and requires a separate operator continuation.

## SQL Agent and pipeline lineage - Prompt 06

Status: **PASS - implementation, focused tests, and full offline regression gate complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Inspect-never-execute boundary

The read-only SQL Agent catalogue query now exposes `js.command` under the explicitly
transient name `command_text_internal`. `prompt05_programmable` passes those fetch rows
directly to the static Agent analyzer. The analyzer removes the transient field before
returning any job, reference, or pipeline mapping; raw command text is therefore absent
from `self.data` and every persistable output.

The analyzer imports no SQL driver, process launcher, shell, package runner, or execution
primitive. It performs only string sanitization, hashing, token inspection, conservative
classification, and mapping construction. SQL Agent job execution remains impossible.

### Persisted command evidence

Each public step row retains its SHA-256 command fingerprint. Full command text is
persisted only for static T-SQL that passes all fail-closed checks: sanitization made no
change, no dynamic SQL was detected, no literals or comments occur, no secret keyword is
present, the length is bounded, and no unsafe control character occurs. All other command
text is discarded.

PowerShell, CmdExec, SSIS, and other non-T-SQL subsystems persist only a generic invocation
hint plus opaque/external classification. Paths, arguments, credentials, connection
details, and package locations do not persist.

### Static SQL Agent reference model

Static T-SQL token analysis conservatively emits:

- `READ` evidence for `FROM` and `JOIN` targets;
- `WRITE` evidence for `INSERT`, `UPDATE`, `DELETE`, and `MERGE` targets;
- `CALL` evidence for statically named `EXEC`/`EXECUTE` targets;
- one-, two-, three-, and four-part target classifications;
- hashed server identity for four-part references;
- opaque external inference for `OPENQUERY`, `OPENROWSET`, and `OPENDATASOURCE`;
- an explicit `DYNAMIC_SQL` opaque row for `sp_executesql`, variable execution, and
  expression-driven execution.

String literals and comments are blanked before token parsing. Dynamic SQL strings are
never interpreted as target evidence. Static parser results remain `INFERENCE`, with
medium or low confidence rather than being promoted to catalog facts.

### New and merged evidence artifacts

Added stable artifact contracts under `16_Pipelines`:

- `SQL_AGENT_STEP_REFERENCES.csv`;
- `SQL_AGENT_PIPELINE_EDGES.csv`.

Both are part of the `agent_jobs` capability contract and receive stable headers even
when SQL Agent metadata is disabled, inaccessible, or empty. Safe Agent edges also merge
into `LINEAGE_EDGES.csv` and `PIPELINE_CATALOGUE.csv`. Those canonical outputs now retain
explicit `evidence_class` fields; opaque/dynamic classifications and external-dependency
flags remain visible.

### Files changed for this gate

- `src/mssql_database_documenter/programmable_queries.py`
- `src/mssql_database_documenter/lineage/agent.py`
- `src/mssql_database_documenter/lineage/__init__.py`
- `src/mssql_database_documenter/contracts.py`
- `src/mssql_database_documenter/fullrun.py`
- `tests/test_agent_lineage.py`

### Verification evidence

| Gate | Result |
|---|---|
| Changed Python modules compile | PASS |
| Focused SQL Agent lineage suite | `11 passed` |
| Full offline regression suite | `124 passed, 2 skipped, 104 subtests passed` |
| SQL Agent catalogue query passes fail-closed SELECT validator | PASS |
| Raw command field absent from persistable in-memory mappings | PASS |
| Static `EXEC` produces conservative `CALL` inference | PASS |
| `INSERT ... SELECT` produces separate `WRITE` and `READ` edges | PASS |
| Three-part name produces cross-database inference | PASS |
| External T-SQL construct is opaque and argument-free | PASS |
| Dynamic SQL is opaque and its literal target is not emitted | PASS |
| PowerShell fixture persists no command/path/argument text | PASS |
| CmdExec fixture is opaque/external | PASS |
| SSIS-like fixture is opaque/external | PASS |
| Fake secret absent from all generated fixture artifacts | PASS |
| Fake secret absent from historical `output/` and `git_export/` | PASS |
| Agent analyzer contains no execution primitives | PASS |
| Both requested CSV contracts and stable headers present | PASS |
| Agent evidence merged into canonical lineage and pipelines | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

The two skips remain the pre-existing Windows symbolic-link privilege cases.

Historical evidence remained at **4,622 files / 55,095,186 bytes**, exactly matching
the Prompt 02 baseline after both Prompt 06 test gates. All SQL Agent tests used temporary
synthetic evidence only.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- SQL Agent command executed: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 06 acceptance requirements: **PASS**.

Prompt 06 is complete. Per the sequential stop rule, Prompt 07 has not been read or
started and requires a separate operator continuation.

## MSSQL metadata completeness - Prompt 07

Status: **PASS - implementation, focused tests, and full offline regression gate complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Whole-database catalogue expansion

Added 13 registered `QuerySpec` catalogues covering the 12 required metadata families;
full-text catalogues and full-text indexes intentionally have separate query and artifact
contracts. Every query has an explicit output schema, stable CSV path, feature-family
identity, and fail-closed `SELECT` validation.

| Required family | Query/artifact evidence |
|---|---|
| Database files | `DATABASE_FILES.csv` (logical metadata only; physical paths omitted) |
| Filegroups | `FILEGROUP_CATALOGUE.csv` |
| Partition functions | `PARTITION_FUNCTIONS.csv` |
| Partition schemes | `PARTITION_SCHEMES.csv` |
| Partition/compression metadata | `PARTITION_COMPRESSION.csv` |
| User-defined alias/table types | `USER_DEFINED_TYPES.csv` |
| Statistics metadata | `STATISTICS_CATALOGUE.csv` |
| Full-text catalog/index metadata | `FULLTEXT_CATALOGUES.csv`, `FULLTEXT_INDEXES.csv` |
| CDC status | `CDC_STATUS.csv` |
| Change Tracking status | `CHANGE_TRACKING_STATUS.csv` |
| Database-scoped configurations | `DATABASE_SCOPED_CONFIGURATIONS.csv` |
| XML schema collections | `XML_SCHEMA_COLLECTIONS.csv` |

Deprecated full-text file-location fields are deliberately omitted. The database-scoped
configuration query uses the SQL Server 2016-compatible column set rather than requiring
the later `is_value_default` column.

### Explicit feature-support evidence

Both the full sequential runner and metadata-only inventory runner now generate:

- `02_Server_Database/MSSQL_FEATURE_SUPPORT_OVERVIEW.csv`;
- `02_Server_Database/MSSQL_FEATURE_SUPPORT_OVERVIEW.md`.

Each registered feature family receives exactly one support row and a stable header-only
catalogue when it produces no data. States are:

- `PRESENT`: the catalog query returned visible rows;
- `ABSENT`: the query succeeded but returned zero rows visible to the reader;
- `INACCESSIBLE`: permission/access evidence prevented a conclusion;
- `UNSUPPORTED`: the SQL Server version or edition lacks the requested catalog surface;
- `DISABLED`: an optional family was explicitly disabled.

The overview warns that SQL Server metadata visibility can limit scope even after a
successful zero-row query. `INACCESSIBLE` and `UNSUPPORTED` are never converted to
`ABSENT`, and errors remain recorded rather than silently omitted.

### Optional security boundary

Added `DISCOVER_SECURITY_METADATA`, default `false`. The optional security query is
registered in every offline SQL-safety gate but runs only when this setting is explicitly
true. Its `SECURITY_PRINCIPALS.csv` output contains structural attributes and SHA-256
principal-name fingerprints; it excludes raw names, SIDs, credentials, and permission
grants. The full runner additionally projects every driver row through the QuerySpec's
explicit columns before persistence, preventing unexpected fields from leaking.

### Contracts and comparisons

All new artifacts are included in the artifact contract and capability matrix. Added
meaningful comparison categories for database files, filegroups, partitioning,
compression, types, statistics, full-text, CDC, Change Tracking, database-scoped
configurations, XML schema collections, opt-in principals, and feature-support states.

### Catalog-schema verification

Version-sensitive fields were checked against Microsoft catalog-view documentation:

- `sys.change_tracking_tables`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/change-tracking-catalog-views-sys-change-tracking-tables
- `sys.database_scoped_configurations`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-database-scoped-configurations-transact-sql
- `sys.fulltext_catalogs`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-fulltext-catalogs-transact-sql
- `sys.xml_schema_collections`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-xml-schema-collections-transact-sql
- `sys.database_principals`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-database-principals-transact-sql

### Files changed for this gate

- `.env.example`
- `README.md`
- `OPERATOR_RUN_GUIDE.md`
- `src/mssql_database_documenter/queries.py`
- `src/mssql_database_documenter/metadata/support.py`
- `src/mssql_database_documenter/metadata/__init__.py`
- `src/mssql_database_documenter/config.py`
- `src/mssql_database_documenter/contracts.py`
- `src/mssql_database_documenter/fullrun.py`
- `src/mssql_database_documenter/inventory.py`
- `src/mssql_database_documenter/comparison/engine.py`
- `src/mssql_database_documenter/cli.py`
- `src/mssql_database_documenter/web/api.py`
- `tests/test_metadata_completeness.py`
- `tests/test_config.py`
- `tests/test_fullrun.py`

### Verification evidence

| Gate | Result |
|---|---|
| Changed Python modules compile | PASS |
| Focused metadata/config/inventory/full-run/comparison suite | `54 passed, 129 subtests passed` |
| Full offline regression suite | `133 passed, 2 skipped, 174 subtests passed` |
| Required logical metadata families represented | PASS; 12 families / 13 QuerySpecs |
| Registered metadata/security SQL safety | PASS; 23 SELECT-only QuerySpecs |
| Explicit columns and unique headers for every family | PASS |
| Artifact and capability contracts for every family | PASS |
| Full runner writes every family artifact and support row | PASS |
| Metadata-only runner writes every family artifact and support row | PASS |
| PRESENT/ABSENT/INACCESSIBLE/UNSUPPORTED state fixtures | PASS |
| Optional security defaults disabled | PASS |
| Enabled security query hashes principal identity | PASS |
| Unexpected raw principal field discarded before persistence | PASS |
| Database file catalogue omits physical paths | PASS |
| Meaningful comparison category for every new output | PASS |
| CLI, Web dry-run, pre-run, and final safety registries include optional query | PASS |
| Historical evidence file and byte counts unchanged | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

The two skips remain the pre-existing Windows symbolic-link privilege cases.

Historical evidence remained at **4,622 files / 55,095,186 bytes**, exactly matching
the Prompt 02 baseline. All Prompt 07 state and persistence tests used temporary
synthetic evidence only.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 07 acceptance requirements: **PASS**.

Prompt 07 is complete. Per the sequential stop rule, Prompt 08 has not been read or
started and requires a separate operator continuation.

## Modularize fullrun.py - Prompt 08

Status: **PASS - incremental modular extraction and offline acceptance gates complete**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Characterization-first execution

Before extraction, `tests/test_fullrun_characterization.py` froze the public stage API,
static SQL/helper semantics, pipeline evidence/header shape, and narrative/control-file
content. Its baseline passed (`4 passed`) before the first implementation move. Each
domain was then extracted and tested before the next domain began.

One lineage gate correctly stopped on a lost `@staticmethod` decorator. The decorator
was restored, the accidentally orphaned decorator was removed from the next monolith
method, and the same gate passed before work continued.

### Ownership result

`fullrun.py` is now 364 lines, down from 1,677 (1,313 lines / 78.3%). It owns run state,
sequential gates, cancellation/errors, connection lifecycle, core metadata acquisition,
safety stages, and orchestration. Domain ownership is now:

- `profiling/`: sensitivity, sampling, table/column profiling and policy;
- `relationships/`: inference, cardinality, FK validation and orphan analysis;
- `lineage/`: static SQL, dependencies, SQL Agent and pipeline evidence;
- `analysis/`: classification, duplicate candidates, quality and risk;
- `reporting/`: object docs, diagrams, narratives, HTML, control files and manifests;
- `runtime.py`: shared serialization, identifier, object-key and safety adapters.

No domain stage module imports `fullrun.py`. `SequentialRun` inherits the domain mixins,
and compatibility aliases preserve the existing helper import surface. The generated
final code review now audits the new ownership and resolves source locations at their
actual module paths. Full details are in `FULLRUN_MODULARIZATION_AUDIT.md`.

### Files added for this gate

- `FULLRUN_MODULARIZATION_AUDIT.md`
- `src/mssql_database_documenter/runtime.py`
- `src/mssql_database_documenter/profiling/policy.py`
- `src/mssql_database_documenter/profiling/stages.py`
- `src/mssql_database_documenter/relationships/inference.py`
- `src/mssql_database_documenter/relationships/stages.py`
- `src/mssql_database_documenter/lineage/static_sql.py`
- `src/mssql_database_documenter/lineage/stages.py`
- `src/mssql_database_documenter/analysis/stages.py`
- `src/mssql_database_documenter/reporting/stages.py`
- `tests/test_fullrun_characterization.py`
- `tests/test_fullrun_modularization.py`

### Verification evidence

| Gate | Result |
|---|---|
| Pre-extraction characterization baseline | `4 passed` |
| Helper compatibility gate | `23 passed, 70 subtests passed` |
| Profiling extraction gate | `43 passed, 85 subtests passed` |
| Relationship extraction gate | `30 passed, 72 subtests passed` |
| Lineage extraction gate | `34 passed, 70 subtests passed` |
| Analysis extraction gate | `30 passed, 72 subtests passed` |
| Reporting extraction gate | `27 passed, 70 subtests passed` |
| Modular ownership/characterization gate | `38 passed, 93 subtests passed` |
| Final full offline regression suite | `141 passed, 2 skipped, 197 subtests passed` |
| Python source/test compile audit | PASS; 70 files |
| `fullrun.py` reduction | PASS; 1,677 to 364 lines (78.3%) |
| Domain modules import `fullrun.py` | PASS; none |
| Public stage and helper compatibility | PASS |
| Read-only guard modules changed by Prompt 08 | PASS; no |
| Historical evidence file and byte counts unchanged | PASS |
| `git diff --check` | PASS; only informational Windows LF/CRLF notices |

Historical evidence remains **4,622 files / 55,095,186 bytes**, exactly matching the
Prompt 02 baseline. No output-contract change was detected by characterization or the
offline regression suite.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 08 acceptance requirements: **PASS**.

Prompt 08 is complete. Per the sequential stop rule, Prompt 09 has not been read or
started and requires a separate operator continuation.

## Runtime self-test decoupling - Prompt 09

Status: **PASS - runtime discovery and developer testing are fully decoupled**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Runtime stage 21

Removed the pytest subprocess from `prompt21_review`. Runtime review now retains only
current-run and installed-package invariants:

- all discovered tables and programmable objects have their required documents;
- object documents contain their semantic contract sections;
- diagrams contain real metadata rather than the old placeholder;
- required outputs are present;
- all registered SQL passes the fail-closed read-only validator;
- comparison capability remains importable;
- installed runtime Python files compile and receive file hashes;
- safety, masking, stage-gate, output, and manifest source anchors remain locatable.

Stage 21 resolves only the installed `mssql_database_documenter` package and does not
read the repository `tests/` tree. A test executes stage 21 with `pytest` unavailable
and `subprocess.run` patched to fail on use; the runtime review completes and records
that developer pytest was not invoked.

### Explicit offline self-test

Added:

```powershell
.\.venv\Scripts\python.exe main.py self-test
```

The command bypasses `.env`/`Settings` loading and invokes pytest only from the isolated
`selftest.py` module. Its immutable argv is:

```text
<current-python> -m pytest -q -p no:cacheprovider -m "not live" tests
```

Execution uses `shell=False`, captured output, a 180-second timeout, disabled bytecode
and pytest-cache creation, and a sanitized bounded summary. It reports failure cleanly
when pytest is unavailable. Tests marked `live` are excluded through the registered
pytest marker.

The optional Web self-test was deliberately not implemented. `self-test` is absent from
the Web allowlist and API surface, so developer testing cannot become a discovery/Web
job accidentally.

### Documentation

`README.md` and `OPERATOR_RUN_GUIDE.md` now explain that:

- discovery never invokes pytest and works without pytest or test source;
- self-test is an explicit offline developer action;
- self-test does not load database configuration, connect, or create discovery/export
  evidence;
- the Web UI intentionally exposes no self-test action.

### Files changed for this gate

- `main.py`
- `pyproject.toml`
- `README.md`
- `OPERATOR_RUN_GUIDE.md`
- `FULLRUN_MODULARIZATION_AUDIT.md`
- `src/mssql_database_documenter/selftest.py`
- `src/mssql_database_documenter/reporting/stages.py`
- `tests/test_runtime_self_test.py`
- `V3_1_REMEDIATION_REPORT.md`

### Verification evidence

| Gate | Result |
|---|---|
| Pre-implementation contract gate | Expected collection failure: self-test module absent |
| Focused runtime/launcher/Web regression gate | `25 passed, 35 subtests passed` |
| Runtime stage with pytest unavailable and subprocess forbidden | PASS |
| Fixed self-test argv and `shell=False` | PASS |
| Self-test bypasses `.env`/Settings | PASS |
| Self-test invokes no connection or run-directory API | PASS |
| Self-test failure summary redaction | PASS |
| Web self-test action/API absent | PASS |
| Actual `python main.py self-test` | PASS; `145 passed, 2 skipped, 197 subtests passed` |
| Final full offline regression suite | `145 passed, 2 skipped, 197 subtests passed` |
| Runtime/pytest subprocess static boundary audit | PASS |
| Python source/test compile audit | PASS; 72 files |
| Historical evidence before/after self-test | PASS; unchanged |

Historical evidence remains **4,622 files / 55,095,186 bytes**:

- `output/`: 2,311 files / 27,547,593 bytes before and after self-test;
- `git_export/`: 2,311 files / 27,547,593 bytes before and after self-test.

The two skipped tests remain the pre-existing Windows symbolic-link privilege cases.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Runtime discovery invokes pytest: **No**.
- Prompt 09 acceptance requirements: **PASS**.

Prompt 09 is complete. Per the sequential stop rule, Prompt 10 has not been read or
started and requires a separate operator continuation.

## Comparison semantics and export presentation - Prompt 10

Status: **PASS - three-run filtering, totals, and static HTML export corrected**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Complete timeline filtering

Comparison status matching now evaluates the union of:

- the row's primary/headline status;
- every A-to-B, B-to-C, and A-to-C interval status;
- every `timeline_events` value.

Consequently, an `absent -> added -> changed` object matches both Added and Changed,
remove/re-add histories match both Removed and Added, and reverted histories remain
visible under Changed. The Web API and browser use the same shared matcher.

The browser now displays timeline events as a separate column and explains that one row
can legitimately appear under more than one event filter.

### Mathematically scoped summaries

Comparison schema version is now 4. The former partial flat totals were replaced with
explicit summaries containing:

- `scope`;
- `row_count`;
- exact `primary_status_counts` that sum to `row_count`;
- interval-status occurrence counts;
- timeline-event occurrence counts;
- a counting note explaining that event occurrences can exceed row counts.

Every category carries a `CATEGORY_ALL_ROWS` summary. The top-level
`GLOBAL_ALL_CATEGORY_ROWS` summary counts every row across every returned category,
including database summary, data types, definition hashes, quality, and coverage. It
also reports per-category row counts. Filtered API responses carry a
`CATEGORY_FILTERED_ROWS` summary whose row count equals the filtered total, independent
of pagination. The browser labels global and selected-category scopes separately.

### Static human-readable HTML

The HTML exporter no longer embeds a JSON payload or uses JavaScript. Python renders a
complete static document with:

- Run A/B/C metadata;
- warnings and the semantic boundary note;
- global and per-category summaries;
- category source, availability, and evidence status;
- every identity and primary status;
- all A/B/C values and A-to-B/B-to-C/A-to-C statuses;
- timeline events;
- numeric values, absolute deltas, and percentage deltas;
- definition sources and unified interval diffs.

All dynamic text is HTML escaped. The safe browser renderer retains the visible report
structure and evidence after removing CSS; no script is needed. JSON remains the full
canonical structured result. CSV remains the canonical flat row export and now includes
the `timeline_events` field.

### Files changed for this gate

- `README.md`
- `OPERATOR_RUN_GUIDE.md`
- `src/mssql_database_documenter/comparison/__init__.py`
- `src/mssql_database_documenter/comparison/diff.py`
- `src/mssql_database_documenter/comparison/engine.py`
- `src/mssql_database_documenter/comparison/exporters.py`
- `src/mssql_database_documenter/web/compare_api.py`
- `src/mssql_database_documenter/web/static/js/compare.js`
- `src/mssql_database_documenter/web/templates/compare.html`
- `tests/test_comparison.py`
- `tests/test_web_app.py`
- `V3_1_REMEDIATION_REPORT.md`

### Verification evidence

| Gate | Result |
|---|---|
| Pre-implementation contract gate | Expected collection failure: event-aware matcher absent |
| Multi-event core filter fixtures | PASS; added+changed, remove+re-add, and reverted |
| Three-run Web API filter fixture | PASS; same row returned by Added and Changed |
| Filtered category summary arithmetic | PASS |
| Global/category summary arithmetic | PASS across every returned category |
| Static HTML contains Run A/B/C and all intervals | PASS |
| Static HTML contains warnings and scoped summaries | PASS |
| Static HTML contains timeline events and numeric deltas | PASS |
| Static HTML contains definition sources/diffs | PASS |
| Static HTML contains no `<script>` dependency | PASS |
| Safe renderer retains useful comparison content | PASS |
| Canonical JSON schema version and summary | PASS; version 4 |
| Canonical CSV timeline events | PASS |
| Focused comparison/renderer/Web suite | `29 passed, 56 subtests passed` |
| Final explicit offline self-test | `148 passed, 2 skipped, 241 subtests passed` |
| Python source/test compile audit | PASS; 72 files |
| Browser comparison JavaScript syntax | PASS |
| `git diff --check` | PASS; informational Windows LF/CRLF notices only |
| Historical evidence before/after tests | PASS; unchanged |

Historical evidence remains **4,622 files / 55,095,186 bytes**:

- `output/`: 2,311 files / 27,547,593 bytes;
- `git_export/`: 2,311 files / 27,547,593 bytes.

The two skipped tests remain the pre-existing Windows symbolic-link privilege cases.
All generated comparison exports used temporary test directories.

### Gate declaration

- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output/` or `git_export/` evidence changed: **No**.
- Real discovery run or Git export created: **No**.
- Prompt 10 acceptance requirements: **PASS**.

Prompt 10 is complete. Per the sequential stop rule, Prompt 11 has not been read or
started and requires a separate operator continuation.

## Offline regression and security gate - Prompt 13

Status: **FAIL - P1 configured-root containment boundary; gate stopped before live validation**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection and no historical evidence mutation

### Completed pre-live gates

| Gate | Exact result |
|---|---|
| Python compilation | PASS: `python -m compileall -q main.py src` |
| Primary imports | PASS: launcher, package, CLI, full run, report regeneration and Web application factory |
| Launcher help | PASS: exit 0; read-only dashboard help displayed |
| Explicit local self-test | PASS: `153 passed, 2 skipped, 241 subtests passed in 5.70s` |
| Self-test connection/evidence declaration | PASS: `connection_attempted=false`, `output_or_export_created=false` |
| Registered-query dry-run | PASS: 35 query specifications; `connection_attempted=false`; resolved mode `metadata+logic` |
| Complete direct offline pytest | PASS: `153 passed, 2 skipped, 241 subtests passed in 5.39s` |
| Dedicated SQL registry/execution group | PASS: `62 passed, 144 subtests passed in 1.50s` |
| Import laziness | PASS: `test_import_has_no_output_or_git_export_side_effects` |
| `create_app` and Help laziness | PASS: application factory and Help requests created no runtime roots and opened no DB connection |
| Self-test laziness | PASS: fixed argv, `shell=False`, no environment loading, connection or run-directory creation |
| Dry-run laziness | PASS: CLI and Web dry-run paths validated registered SQL without a connection or output root |
| In-memory comparison laziness | PASS: `export=false` returned no exports and created no `output/comparisons` directory |

### Required unsafe-execution review

| Surface | Review result |
|---|---|
| `subprocess` | One production call in `selftest.py`; fixed interpreter/pytest argv, fixed project cwd, `shell=False`, sanitized summary |
| `os.system`, `eval`, `exec`, `shell=True` | No production matches |
| SQL execution | Application call sites use `ReadOnlyCursor`; the raw driver call exists only inside its final-boundary wrapper after `validate_read_only_sql` |
| Arbitrary shell/SQL Web APIs | None; state-changing actions use the closed allowlist and CSRF/same-origin checks |
| Network binding | Web configuration rejects non-loopback hosts before `app.run`; debug and reloader are disabled |
| Secret echo | Configuration and job diagnostics use sanitized views/redaction; no credential output path found |
| Sensitive sample Git export | Raw payload mode is unavailable; default excludes payloads and `masked_only` masks every retained non-empty cell before the independent audit |
| HTML | Comparison/report values are escaped; Markdown and trusted generated HTML are sanitized with Bleach; executable tags and unsafe protocols are removed |
| File browsing | Absolute/traversal paths and resolved targets outside configured roots are rejected |
| Publication path containment | **P1 FAIL**, detailed below |

### P1 stop condition - nested junction/symlink publication escape

The publication APIs sanitize user-derived path components, but they do not all
validate every existing destination ancestor before creating or copying files. A
pre-existing nested Windows junction or symbolic link can therefore redirect writes
outside the configured root:

1. **Git export:** `git_export.py:160` constructs the target below the resolved
   root, but `git_export.py:208-209` creates the parent and calls
   `shutil.copytree` without resolving the completed target back under
   `git_export_root`. A junction at `git_export_root/MSSQL` or a database
   component can redirect the published export.
2. **Comparison export:** `comparison/exporters.py:134-142` constructs and creates
   `output_root/comparisons/compare_*` without a destination containment or
   reparse-point check. A junction at `output_root/comparisons` can redirect JSON,
   CSV and HTML writes.
3. **Report regeneration:** `report_regeneration.py:208-214` validates resolved
   containment only after `base.mkdir(parents=True)`. A junction at the database
   component can cause the run-id directory itself to be created outside
   `output_root` before the operation detects and rejects the escape.

Severity is P1 because an explicit local Web/CLI publication action can write outside
its configured evidence root when a writable nested reparse point is pre-positioned.
No exploit was executed against user evidence; the failure follows directly from the
reviewed create/copy order.

Required remediation is to validate each destination ancestor before descending,
reject symlinks/reparse points, resolve the final parent under its configured root
before any write, recheck immediately before publication, and add Windows
junction/symlink regression fixtures for all three paths.

### Historical evidence integrity

The combined `output/` and `git_export/` fingerprint was identical before and
after the completed Prompt 13 gates:

| Measurement | Before | After |
|---|---:|---:|
| Files | 4,622 | 4,622 |
| Bytes | 55,095,186 | 55,095,186 |
| Content/path tree SHA-256 | `e16a2a61170e81e5f4034ccf2107434103f172da422cff2b5f73e8b23e93c8b6` | `e16a2a61170e81e5f4034ccf2107434103f172da422cff2b5f73e8b23e93c8b6` |

### Mandatory stop declaration

- P0/P1 gate status: **P1 FAIL**.
- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Runtime discovery run or real export created: **No**.
- Historical evidence changed: **No**.
- Dedicated Web, masking/export, comparison and report-regeneration reruns after the
  source review: **NOT RUN due to mandatory P1 stop**. These tests did pass inside
  both complete offline suites above, but no later gate was started after the P1 was
  identified.
- Prompt 13 acceptance status: **BLOCKED pending containment remediation and a clean
  restart of Prompt 13**.

Prompt 13 stopped at the P1 gate. No live-validation prompt was read or executed.

### Prompt 13 rerun attempt - unresolved P1 preflight stop

Recorded: 2026-09-06  
Status: **FAIL - previously reported P1 remains unchanged**

The operator requested a fresh Prompt 13 run. Before re-entering the ordered gate,
the three previously failing publication boundaries were compared with the recorded
finding. No containment remediation is present:

- `git_export.py:160,208-209` still constructs the target and then creates/copies
  through nested ancestors without resolving the completed parent beneath
  `git_export_root`;
- `comparison/exporters.py:134-142` still creates the comparison destination
  without a configured-root containment or reparse-point check;
- `report_regeneration.py:208-214` still calls
  `base.mkdir(parents=True)` before validating the resolved base beneath
  `output_root`.

Because Prompt 13 states “If any P0/P1 fails: STOP,” the rerun stopped at this
preflight. Compile, test and subgroup gates were not repeated, no repair was made,
no output/export action ran, and no MSSQL connection was attempted. Prompt 13
remains blocked until these containment paths are remediated and covered by
Windows junction/symlink regression tests.

## Python environment and P1 containment remediation

Status: **PASS - environment repaired and P1 publication escape closed**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection or historical evidence mutation

### Python and dependency verification

| Check | Result |
|---|---|
| System `python` | Python 3.11.9 at `C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe` |
| Python launcher default | Python 3.13 |
| Project virtual environment | Isolated Python 3.13.14 at `.venv\Scripts\python.exe` |
| Project requirement | Compatible: `requires-python >=3.11` |
| Initial editable package state | Stale: pointed to the former `SchoolERP_DB_Discovery\MSSQL` project path |
| Editable package repair | Reinstalled with isolated declared setuptools build tooling; now points to `D:\School ERP projects\Database_Discovery_Tool` |
| Required imports | PASS: project package, Flask, pyodbc, python-dotenv, Markdown, bleach and pytest |
| Dependency consistency | PASS: `pip check` reports no broken requirements |
| Installed ODBC visibility | PASS: pyodbc imported and enumerated six local drivers without connecting |
| Optional analysis extra | Not installed and not required: no production/test Python source imports pandas, sqlparse, networkx or standalone Jinja2 APIs |

Installed relevant versions are Flask 3.1.3, pyodbc 5.3.0,
python-dotenv 1.2.3, Markdown 3.10.3, bleach 6.4.0, Jinja2 3.1.6,
MarkupSafe 3.0.3 and pytest 9.1.1. The old generated `command` entry in
`.venv/pyvenv.cfg` records where the environment was originally created, but the
active executable, prefix, dependencies and repaired editable link all resolve to
the current repository.

The earlier ad-hoc combination of system Python 3.11 with the Python 3.13
`.venv/Lib/site-packages` directory was invalid for compiled wheels. Validation now
uses the virtual environment's own interpreter end to end.

### P1 root cause and implementation

Root cause: Git, comparison and report publication constructed descendant paths with
recursive `mkdir` or `copytree` before every existing ancestor had been inspected.
A pre-positioned Windows directory junction could therefore redirect a write beyond
the configured root.

Added `src/mssql_database_documenter/path_safety.py` with one shared fail-closed
boundary:

- canonicalizes the explicitly configured root;
- validates every relative component;
- detects broken links, symbolic links, Windows junctions and other reparse points
  without following them;
- creates descendants exactly one level at a time;
- verifies resolved containment after every level;
- requires publication leaf paths to be nonexistent;
- supports post-copy/post-rename containment revalidation.

Integration changes:

- Git export prepares and revalidates
  `MSSQL/<database>/run_<id>` through the shared guard before/after `copytree`;
- comparison export safely creates `comparisons/compare_<timestamp>` before writing
  JSON, CSV or HTML;
- report regeneration validates its database/run hierarchy before creating staging,
  rechecks staging before rename, and validates the published destination afterward;
- source evidence junctions/reparse points are rejected by both Git export and report
  regeneration.

### Verification evidence

| Gate | Result |
|---|---|
| Real Windows junction regression fixtures | PASS: 4/4, no privilege skip |
| Junction targets remained empty after rejection | PASS for shared guard, Git export, comparison export and report regeneration |
| Focused containment/export/comparison/report suite | `20 passed, 44 subtests passed in 2.73s` |
| Complete virtual-environment self-test | `157 passed, 2 skipped, 241 subtests passed in 5.75s` |
| Self-test safety fields | `connection_attempted=false`, `output_or_export_created=false` |
| Virtual-environment launcher help | PASS |
| Virtual-environment dry-run | PASS: 35 registered SQL specifications, `connection_attempted=false` |
| Production unsafe-execution scan | Only fixed-argv self-test subprocess; no `os.system`, `eval`, `exec` or `shell=True` |
| SQL execution boundary review | PASS: raw driver execution remains inside `ReadOnlyCursor` after fail-closed validation |
| Changed-source compile/import | PASS |
| `git diff --check` | PASS; informational Windows LF/CRLF notices only |

Historical evidence remained byte-identical:

- files: 4,622 before and after;
- bytes: 55,095,186 before and after;
- content/path tree SHA-256:
  `e16a2a61170e81e5f4034ccf2107434103f172da422cff2b5f73e8b23e93c8b6`.

### Repair declaration

- Previously reported P1 containment finding: **REMEDIATED**.
- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Real discovery/export/comparison/regeneration output created: **No**.
- Historical evidence changed: **No**.
- The offline Prompt 13 gate is eligible for a clean rerun.

## Prompt 13 clean rerun - Offline Regression and Security Gate

Status: **PASS**  
Recorded: 2026-09-06  
Execution boundary: offline only; no MSSQL connection

Prompt 13 was rerun sequentially from its first gate after the containment repair.
No later prompt was read or executed.

### Exact gate evidence

| Ordered gate | Exact result |
|---|---|
| Historical evidence baseline | `4622 files`, `55095186 bytes`, tree SHA-256 `e16a2a61170e81e5f4034ccf2107434103f172da422cff2b5f73e8b23e93c8b6` |
| Compile | PASS: `.venv\\Scripts\\python.exe -m compileall -q main.py src` |
| Imports | PASS: `main`, package, CLI, full-run, report-regeneration, path-safety and Web app modules |
| CLI help | PASS, exit 0; top-level commands are `web`, `self-test`, `test-connection`, and `cli` |
| Runtime self-test | `157 passed, 2 skipped, 241 subtests passed in 6.04s`; status PASS, `connection_attempted=false`, `output_or_export_created=false` |
| Dry-run | PASS; 35 registered SQL specifications validated; resolved mode `metadata+logic`; `connection_attempted=false` |
| Complete offline pytest | `157 passed, 2 skipped, 241 subtests passed in 6.25s` |
| SQL registry/guard suite | `62 passed, 144 subtests passed in 1.28s` |
| Web/security suite | `48 passed, 2 skipped, 15 subtests passed in 2.85s` |
| Masking/export/containment suite | `24 passed, 13 subtests passed in 0.86s` |
| Comparison suite | `11 passed, 44 subtests passed in 0.96s` |
| Report-regeneration/containment suite | `6 passed in 1.01s` |
| Focused laziness proof | `6 passed in 1.47s` |
| Historical evidence after all gates | `4622 files`, `55095186 bytes`, tree SHA-256 `e16a2a61170e81e5f4034ccf2107434103f172da422cff2b5f73e8b23e93c8b6` |

The complete offline suite's two skips are the existing platform/availability skips;
they are not failures. The Windows junction containment fixtures ran in the
masking/export/containment and report-regeneration groups without a privilege skip.

### Explicit laziness proof

The focused six-test run proves each required boundary independently:

- import: importing `main` and `mssql_database_documenter.fullrun` creates neither
  `output` nor `git_export`;
- `create_app`: constructing the Flask app and serving its dashboard creates no
  runtime roots, and a non-loopback host is rejected;
- help: `main.py --help` exits successfully without invoking discovery;
- self-test: uses a fixed argument vector, `shell=False`, does not call the database
  connector or run-directory creator, and creates no runtime roots;
- dry-run: validates the allowlisted SQL registry, completes without a database
  connection, and creates no `output` directory;
- in-memory comparison: `export=false` returns no export paths and creates no
  `output/comparisons` directory.

### Required source security review

- Process execution: the only production subprocess call is the explicit offline
  self-test. It uses the constant `SELF_TEST_ARGV`, `shell=False`, a fixed project
  working directory, a timeout, and sanitized output. No production `os.system`,
  `eval`, `exec`, or `shell=True` path exists.
- SQL execution: all production `cursor.execute` call sites use `ReadOnlyCursor`
  and/or immediately call `validate_read_only_sql`; the raw driver call exists only
  inside `ReadOnlyCursor.execute` after fail-closed validation. `executemany` is
  disabled. Registry and dynamic sampling SQL are covered by the SQL safety tests.
- File copy and publication: Git export rejects source links/reparse points, copies
  into an isolated temporary staging directory, audits that staging tree, obtains a
  new contained destination, then revalidates after `copytree`. Comparison and
  report-regeneration destinations pass through the shared component-by-component
  containment guard; report staging is rechecked before and after rename.
- Path resolution: the Web file browser canonicalizes roots, rejects traversal and
  out-of-root resolution, and the publication guard rejects symbolic links,
  junctions, reparse points, invalid components, existing leaves, and resolved
  escape attempts. Real Windows-junction regressions pass and outside targets remain
  untouched.
- HTML: generated comparison/report fields use `html.escape`; rendered Markdown and
  report HTML pass through explicit `bleach` tag/attribute/protocol allowlists;
  executable elements are stripped and templates retain automatic escaping.
- Network binding: Web configuration accepts only `127.0.0.1`, `localhost`, or
  `::1`; `0.0.0.0` is rejected, and Flask runs with debug and reloader disabled.
- Secrets and samples: configuration output uses sanitized values, exception/job
  output is redacted, Git export permits only `exclude` or `masked_only`, raw sample
  export is forbidden, every included non-empty sample cell is masked in staging,
  and an independent fail-closed evidence audit runs before publication.
- Arbitrary interfaces: Web action names are allowlisted; shell/SQL/eval/Python API
  endpoints are absent; CSRF, same-origin, and security-header tests pass.

### Prompt 13 gate declaration

- P0 failures: **none**.
- P1 failures: **none**.
- Previously reported publication-containment P1: **remediated and regression-tested**.
- Live MSSQL database touched: **No**.
- MSSQL connection attempted: **No**.
- Historical `output` or `git_export` evidence changed: **No**.
- Prompt 13: **COMPLETE**.

## Prompt 14 - Live Read-Only Validation

Status: **STOPPED - DB1 safe-profile safety gate failed**  
Recorded: 2026-09-06  
Authorization: the operator explicitly authorized Prompt 14 live-readonly access

Prompt 14 was executed in its required DB1-first order. The run stopped before DB2
because DB1 did not pass every required stage. Full-readonly was not separately
authorized and was not run.

### DB1 ordered evidence

Database: `Chikhali SchoolERP`

| Gate | Exact result |
|---|---|
| Dry-run | PASS; 35 registered SQL specifications; resolved mode `metadata+logic`; `connection_attempted=false` |
| Connection test | PASS; three guarded result sets: `connection_identity`, `server_capabilities`, `database_capabilities`; three total rows |
| Metadata run | `20260906_150548`; `COMPLETED`; mode `metadata`; coverage `20/20`; 14 PASS and 6 `SKIPPED_BY_MODE`; 0 errors; 0 warnings |
| Metadata evidence | 159 files, 878,535 bytes; 158 checksum entries, 0 mismatches; 0 sample payload CSVs |
| Metadata safety | Embedded audit PASS; independent audit PASS across 159 files with 0 violations |
| Metadata+logic run | `20260906_150721`; `COMPLETED`; coverage `20/20`; 17 PASS and 3 `SKIPPED_BY_MODE`; 0 errors; 0 warnings |
| Metadata+logic evidence | 986 files, 11,877,512 bytes; 985 checksum entries, 0 mismatches; embedded and independent audits PASS with 0 violations |
| Safe-profile run | `20260906_150848`; `FAILED`; coverage `15/20`; 15 PASS and 1 FAILED; final Git/evidence safety gate rejected publication eligibility |

The metadata+logic run discovered 2 views, 809 stored procedures, 11 functions,
3,541 parameters, 2,545 object-dependency rows, 4,651 lineage edges, 3 SQL
Agent jobs, 4 SQL Agent step references, and 4 SQL Agent pipeline edges. It created
no sample payload CSVs.

### DB1 safe-profile inspection

- Sampling controls: 74 objects attempted (72 tables and 2 views); 63 `SAMPLED`,
  10 `EMPTY`, and 1 `INACCESSIBLE`; 1,974 rows returned in total.
- View sampling: `dbo.paystudcount` returned 50 bounded rows and was sampled;
  `dbo.feespegv` was inaccessible because SQL Server reported invalid-column/binding
  errors. The object-level limitation was recorded and the sampling stage continued.
- Large-table policy: threshold 1,000,000 rows, large-table sampling enabled; no
  table exceeded the threshold in `TABLE_SIZE_PROFILE.csv`, so there was no
  large-table sample status to exercise for DB1.
- Sensitivity: 806 columns classified: 644 `Unknown`, 132 `PII`, 15 `Financial`,
  12 `Potentially Sensitive`, and 3 `Credential`; 162 columns were in a sensitive
  category.
- Masking controls: sample masking was enabled; the safety audit checked 11,538
  sensitive persisted values. `sample_values_masked=true`, while
  `profile_values_masked=false` due to the single violation below.
- SQL Agent evidence: 3 jobs, 4 step references, and 4 pipeline edges.
- Additional MSSQL metadata included 2 database files, 1 filegroup, 73
  partition/compression rows, 795 statistics rows, and 41 database-scoped
  configuration rows. Partition functions/schemes, user-defined types, full-text,
  CDC, change tracking, XML schema collections, and security principals were
  represented by empty/header-only artifacts where unavailable or not present.

### Blocking safety finding

The embedded evidence audit failed with exactly one violation:

`unmasked PII value in COLUMN_PROFILE.csv row 213, field maximum_value`

The affected identity is `dbo.FeeMstStudent.outwardno` (`varchar`). No underlying
database value is reproduced here. Safe structural observations only:

- the persisted maximum is non-empty, eight characters long, and does not use the
  required `[MASKED:...]` token;
- the earlier column-profile classification was `Unknown` / `PRESERVE` /
  `NO_SENSITIVITY_SIGNAL`;
- later sampled-value classification upgraded the same column to high-confidence
  `PII` / `PSEUDONYMIZE` based on `VALUE_SIGNAL: phone value pattern`;
- masking was enabled, but the already-persisted column-profile maximum was not
  remasked after the stronger sampling classification became available;
- the final fail-closed audit applied the stronger classification and correctly
  stopped the pipeline.

This is a P1 sensitive-evidence consistency defect. The failed run is not eligible
for Git export or use as a passing live-validation run.

### Stop declaration

- DB1 passed all Prompt 14 gates: **No**.
- Git export performed: **No**; zero export paths match any new run ID.
- DB2 accessed: **No**.
- Three-run comparison performed: **No**.
- Static comparison HTML opened: **No**.
- Full-readonly performed: **No; not separately authorized**.
- Prompt 14 completion: **BLOCKED at DB1 safe-profile safety audit**.

Per the prompt's DB1-before-DB2 gate, execution stopped here. No checks beyond this
point are claimed.

## Prompt 15 - Final Fine-Comb Audit and v3.1 Freeze

Status: **AUDIT COMPLETE - FREEZE DENIED**  
Recorded: 2026-09-06

The final audit covered 182 project-owned implementation, configuration, test,
documentation, and prompt/specification files. The 72 prompt-pack files were
individually inventoried; all 67 entries across their three checksum manifests
matched with zero missing files and zero mismatches.

Static regression review found the remediated controls present for lazy lifecycle,
SELECT-only guarded execution, Agent static analysis without execution, fixed-argv
self-test, distinct mode policies, offline report regeneration, static comparison
HTML, three-run multi-event filtering, metadata contracts, CI, redaction, and guarded
destination paths.

Required documentation was updated:

- `V3_1_FINAL_FILE_AUDIT.md` was created with the per-file audit and acceptance
  disposition;
- `README.md` and `OPERATOR_RUN_GUIDE.md` now state the live-validation hold;
- `SAFETY_MODEL.md` now documents final-classification reconciliation and the
  local-diagnostic-only rule for failed evidence;
- Web Help explains that a failed audit run may retain unsafe local diagnostic
  values and must not be shared or edited into a passing state;
- `HTML_FEATURE_CHECKLIST.md` now says offline `Regenerate Reports` and separates
  UI-feature PASS from product-freeze readiness.

Post-update verification:

- compile: PASS;
- complete offline suite: `157 passed, 2 skipped, 241 subtests passed in 8.00s`;
- prompt-pack checksums: PASS;
- no new live DB action, comparison, full-readonly, or Git export was performed.

Freeze blockers:

1. P1: DB1 safe-profile run `20260906_150848` retains one unmasked profile maximum
   after later sample evidence upgraded the column to PII. The audit caught it, but
   the pipeline does not reconcile/remask the earlier profile artifact.
2. P2: package and generated evidence identify the implementation as `0.3.0`; a
   v3.1 release identity has not been selected and consistently applied or explicitly
   accepted.
3. DB2 and three-run live smoke remain blocked because DB1 did not pass. Full-readonly
   was not separately authorized.

Prompt 15 therefore does not declare the tool ready to freeze. Exact evidence and
the complete file matrix are in `V3_1_FINAL_FILE_AUDIT.md`.

## Post-Prompt-15 remediation - late sensitivity, version, and evidence gaps

Status: **OFFLINE REMEDIATION PASS; LIVE REVALIDATION PENDING**  
Recorded: 2026-09-07

This work repairs the two findings from Prompt 15 without changing or deleting the
failed canonical live run. No MSSQL connection, DB2 action, comparison export, Git
export, or full-readonly action was performed.

### P1 - final-classification reconciliation

Root cause was stage ordering: profile extrema and low-cardinality values could be
written while classified `Unknown`, then bounded sample evidence could produce a
stronger sensitive classification. The final audit correctly evaluated the stronger
classification, but the earlier persisted values had not been reconciled.

`ProfilingStagesMixin` now:

- builds the final sensitivity catalogue from samples/overrides/classifier evidence;
- retains an earlier sensitive profile classification rather than allowing a later
  non-sensitive or unknown result to downgrade it;
- reconciles the final category, action, confidence, and evidence into column-profile
  and low-cardinality rows;
- re-masks profile minimum/maximum and low-cardinality values before the final
  sensitivity artifact and independent safety audit are completed.

The regression starts with an unmasked, `Unknown` profile/low-cardinality value and a
later sample-derived PII result, then asserts the raw value is absent and both stored
values use masked tokens. Focused containment gate: **37 passed, 83 subtests**.
Complete suite immediately after the repair: **158 passed, 2 skipped, 241 subtests**.

Disposition: **P1 implementation defect remediated and offline-tested.** Historical
run `20260906_150848` remains failed/local-only. A fresh DB1 run is required for live
acceptance; historical evidence was not rewritten.

### P2 - v3.1 release identity

The reviewed package version is `0.3.1`. `pyproject.toml` and package `__version__`
now agree; inventory and full-run reporting import that package identity instead of
hard-coding a second version. A regression checks project/package equality and the
v3.1 value. Focused gate: **41 passed, 92 subtests**. Static search found no `0.3.0`
literal in `pyproject.toml` or production package source.

Disposition: **P2 remediated.** Older test fixtures and historical reports may retain
`0.3.0` because they describe old evidence; new runtime evidence uses `0.3.1`.

### Prompt 11 durable execution evidence completion

The implementation was already present, but the remediation report lacked a dedicated
execution section. A fresh focused gate was therefore run after P1/P2 repair:

- report regeneration and its Web action: **3 passed**;
- 12 unrelated Web tests were deliberately deselected by the focused expression;
- tests patch database connection to fail and still prove successful regeneration;
- canonical input hashes remain unchanged; destinations are unique, versioned, and
  contained under `output/report_regenerations/`;
- no claim is made that regeneration refreshes database evidence or creates a Git
  export.

Disposition: **Prompt 11 implementation and durable evidence PASS.** This is a dated
evidence reconstruction, not a fabricated claim about an omitted earlier section.

### Prompt 12 durable execution evidence completion

Fresh sequential evidence after Prompt 11:

- compile/import and package identity: PASS (`0.3.1`);
- CI/runtime self-test contract tests: **6 passed**;
- public `main.py self-test`: **PASS**, reporting **159 passed, 2 skipped, 241
  subtests**;
- self-test result recorded `connection_attempted=false` and
  `output_or_export_created=false`;
- existing runtime-root file counts remained unchanged: output `4514 -> 4514`, Git
  export `2311 -> 2311`.

Disposition: **Prompt 12 implementation and durable evidence PASS.** GitHub workflow
uses Windows/Python 3.11, offline tests, compile/import checks, read-only permissions,
and runtime-root absence assertions without MSSQL credentials.

### Prompt 13 offline regression and security gate rerun

The first fingerprint command used a .NET helper unavailable in the installed
PowerShell runtime. Although all substantive commands passed, that attempt was treated
as incomplete. The fingerprint helper was replaced with a compatible SHA-256 encoding
and every laziness action was repeated before this gate was accepted.

Final evidence:

- compile: PASS;
- package/core/full-run/Web imports and `create_app()`: PASS, version `0.3.1`;
- launcher and package help: PASS;
- public self-test: PASS, **159 passed, 2 skipped, 241 subtests**;
- registered-query dry-run: PASS for 35 SELECT-only queries,
  `connection_attempted=false`;
- independent complete pytest run: **159 passed, 2 skipped, 241 subtests**;
- focused full-run, masking/evidence, Git-export, comparison, regeneration, Web, and
  path-containment gate: **57 passed, 126 subtests**;
- import, `create_app`, help, self-test, dry-run, and in-memory comparison left exact
  output and Git-export file-inventory fingerprints unchanged;
- static review: no `os.system`, production `eval`/`exec`, arbitrary shell/SQL
  endpoint, unguarded execution, non-loopback binding, secret echo, or raw-sensitive
  export path. The sole subprocess is fixed-argv self-test with `shell=False`; cursor
  execution is guarded; copy/rename paths are containment checked; trusted generated
  HTML is sanitized before the template's safe rendering branch.

Disposition: **Prompt 13 PASS with no unresolved offline P0/P1.** Per the remediation
pack, the next gate is a fresh ordered Prompt 14 DB1 live-readonly validation. It must
not begin without explicit live authorization.

### Final local environment acceptance

- project interpreter: Python 3.13.14 in `.venv` (project requirement is Python 3.11+);
- pip: 26.1.2 in the same `.venv`;
- dependency integrity: `pip check` reported no broken requirements;
- editable package was refreshed without dependency changes;
- package `__version__`, installed distribution metadata, and `pyproject.toml` all
  report `0.3.1`;
- console-script help: PASS;
- final complete suite: **159 passed, 2 skipped, 241 subtests**;
- exact output and Git-export inventory fingerprints remained unchanged.

## Prompt 14 rerun - Live Read-Only Validation

Status: **PASS WITH DOCUMENTED OBJECT-LEVEL ACCESS LIMITATIONS**

Recorded: 2026-09-07
Authorization: explicit user authorization received before live access

Execution was strictly sequential. DB2 did not begin until every DB1 gate and
independent evidence inspection passed. Git export did not begin until both generated
and independent masking audits passed. Full-readonly was not separately authorized
and was not run. The failed historical run `20260906_150848` was neither edited nor
used as comparison/export input.

### DB1 - Chikhali SchoolERP

| Gate | Result |
|---|---|
| Registered-query dry-run | PASS; 35 queries SAFE; no connection; metadata policy permits no data scans |
| Read-only connection/capabilities | PASS; three guarded queries; server/login sanitized or redacted |
| Metadata `20260907_014959` | COMPLETED; `0.3.1`; 14 PASS / 6 SKIPPED_BY_MODE; 0 errors/warnings; audit PASS; 158 checksums valid |
| Metadata+logic `20260907_015059` | COMPLETED; `0.3.1`; 17 PASS / 3 SKIPPED_BY_MODE; 0 errors/warnings; audit PASS; 985 checksums valid |
| Safe-profile `20260907_015218` | COMPLETED_WITH_WARNINGS; `0.3.1`; 20/20 PASS; 0 errors, 1 warning; generated and independent audits PASS with 0 violations; 1,059 checksums valid |
| Explicit Git export | `git_export/MSSQL/Chikhali SchoolERP/run_20260907_015218`; policy `exclude`; 0 sample payload CSVs; 0 configured identity/credential hits; independent audit PASS; 986 checksums valid |

Safe-profile inspection:

- 62 user tables sampled, 10 empty; 2 views attempted, 1 sampled and 1 inaccessible;
- inaccessible view `dbo.feespegv` has an existing invalid-column/binding error;
  impact is limited to that object's sample and continuation is recorded explicitly;
- no table exceeded the 1,000,000-row profile threshold, so no live skipped-large
  branch was applicable;
- 795 profile rows, 3,818 low-cardinality rows, 806 masking rows, and 74 bounded local
  sample payloads were produced;
- sensitivity catalogue: Credential 3, Financial 15, PII 132, Potentially Sensitive
  12, Unknown 644;
- former failing identity `dbo.FeeMstStudent.outwardno` is final PII /
  PSEUDONYMIZE / HIGH and both profile extrema are empty or valid masked tokens;
- 4 sanitized SQL Agent references were retained; new feature-state evidence reports
  PRESENT 5, ABSENT 8, DISABLED 1.

### DB2 - Shirgaon SchoolERP

| Gate | Result |
|---|---|
| Registered-query dry-run | PASS; 35 queries SAFE; no connection; metadata policy permits no data scans |
| Read-only connection/capabilities | PASS; three guarded queries; server/login sanitized or redacted |
| Metadata `20260907_015651` | COMPLETED; `0.3.1`; 14 PASS / 6 SKIPPED_BY_MODE; 0 errors/warnings; audit PASS; 269 checksums valid |
| Metadata+logic `20260907_015735` | COMPLETED; `0.3.1`; 17 PASS / 3 SKIPPED_BY_MODE; 0 errors/warnings; audit PASS; 1,101 checksums valid |
| Safe-profile `20260907_015839` | COMPLETED_WITH_WARNINGS; `0.3.1`; 20/20 PASS; 0 errors, 1 warning; generated and independent audits PASS with 0 violations; 1,286 checksums valid |
| Explicit Git export | `git_export/MSSQL/Shirgaon SchoolERP/run_20260907_015839`; policy `exclude`; 0 sample payload CSVs; 0 configured identity/credential hits; independent audit PASS; 1,102 checksums valid |

Safe-profile inspection:

- 105 user tables sampled, 78 empty; 2 views attempted, 1 sampled and 1 inaccessible;
- the inaccessible view is the same truthfully recorded `dbo.feespegv` binding error;
- no table exceeded the 1,000,000-row profile threshold;
- 2,078 profile rows, 6,105 low-cardinality rows, 2,089 masking rows, and 185 bounded
  local sample payloads were produced;
- sensitivity catalogue: Credential 2, Financial 44, Health 1, PII 205, Potentially
  Sensitive 35, Unknown 1,802;
- generated and independent audits found no raw value requiring masking under the
  final catalogue;
- 4 sanitized SQL Agent references were retained; new feature-state evidence reports
  PRESENT 5, ABSENT 8, DISABLED 1.

### Three-run comparison and static presentation

Compatible same-database `0.3.1` runs were selected in chronological mode order:

- A: DB1 metadata `20260907_014959`;
- B: DB1 metadata+logic `20260907_015059`;
- C: DB1 safe-profile `20260907_015218`.

The production comparison completed across 44 categories and 13,147 rows. Because the
modes intentionally differ, it correctly warns that unavailable evidence may not be
comparable. All status filters executed: ADDED 10,896; CHANGED_ONLY 7; REMOVED 0;
UNCHANGED 11,880; NOT_COMPARABLE 0. Two rows carry multiple timeline events, proving
the multi-event path with real evidence.

Explicit static HTML/CSV/JSON output was created at
`output/comparisons/compare_20260907_020748_003358/`. The HTML source contains no
script tag and includes complete run metadata and global/category summaries. The
application's local `/file` route returned HTTP 200; after removing the surrounding
application-shell scripts, the report remained fully readable with run metadata and
global summary intact. Interactive visual browser control was not available in this
session, so no visual-browser claim is made.

Two comparison harness assertions were corrected before acceptance: one mixed an
absolute export path with a relative configured root; another assumed the wrong report
heading. Neither was a product failure, and no duplicate export was created after the
valid comparison directory existed.

### Prompt 14 disposition

- DB1: PASS with one documented object-level view limitation.
- DB2: PASS with one documented object-level view limitation.
- New safe-profile Git exports: PASS, exclude-samples policy verified.
- Three-run comparison/static presentation: PASS; interactive visual browser not
  available and not claimed.
- Full-readonly: NOT RUN; no separate authorization.
- Unresolved live masking/containment P1: none.

Prompt 14 is complete. Per the sequential remediation pack, Prompt 15 final fine-comb
and freeze review has not started and requires a separate instruction.

## Prompt 15 rerun - Final Fine-Comb Audit and v3.1 Freeze

Status: **PASS**

Recorded: 2026-09-07

All 183 current project-owned files were re-audited using the existing exhaustive
per-file matrices plus a current-tree delta review. Coverage includes 52 production
Python files, 13 Web assets, 25 tests, 7 configuration/packaging/CI files, 14 root
launch/report/audit/documentation files, and 72 prompt/specification files. Runtime
evidence, Git exports, `.env`, `.venv`, caches, bytecode, build output, and `.git` are
environment/generated state and were not misclassified as project source.

Evidence:

- remediation pack: 20/20 checksum entries valid;
- configured-value source scan: zero configured server/user/password hits outside
  excluded runtime/private roots;
- required README, operator guide, safety model, Help, checklist, remediation report,
  and final audit: present and non-empty;
- lifecycle, SQL/cursor, discovered code, Agent, subprocess, secret/sample, report
  semantics, HTML, mode, modularity, runtime pytest, metadata, 2/3-run, filter, CI, and
  containment searches: PASS;
- Python 3.13.14 and `pip check`: PASS;
- project/package/distribution version: `0.3.1`;
- compile/import/`create_app`/launcher help/non-connecting 35-query dry-run: PASS;
- explicit self-test: **159 passed, 2 skipped, 241 subtests**;
- independent offline suite: **159 passed, 2 skipped, 241 subtests**;
- output and Git-export inventory fingerprints unchanged during the offline gate;
- Prompt 14 DB1/DB2 safe-profile audits, independent re-audits, Git exports,
  checksums, and A/B/C comparison: PASS as recorded above.

Accepted limitations are not hidden: both safe-profile runs record one object-level
sample warning for the database-owned broken view `dbo.feespegv`; interactive visual
browser control was unavailable, while the real local file route and script-independent
report contract passed; full-readonly was not separately authorized and was not rerun.
None is an unresolved source P0/P1/P2 or invalidates the authorized live safety gate.

Final disposition:

- unresolved P0: **0**;
- unresolved P1: **0**;
- unresolved P2: **0**;
- offline gate: **PASS**;
- authorized live gate: **PASS WITH DOCUMENTED OBJECT-LEVEL LIMITATIONS**;
- required documentation: **PASS**;
- Git commit/tag/release/deployment: not requested and not performed.

**MSSQL DOCUMENTATION TOOL v3.1 — READY TO FREEZE**
