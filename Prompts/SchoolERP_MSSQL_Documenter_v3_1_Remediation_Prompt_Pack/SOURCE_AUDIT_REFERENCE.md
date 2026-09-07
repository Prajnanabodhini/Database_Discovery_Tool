# Database_Discovery_Tool — Independent Fine-Comb Audit

**Repository:** `Prajnanabodhini/Database_Discovery_Tool`  
**Branch:** `main`  
**Audited commit:** `1c608d12d7c0f107931144dbbdc4e536865ab546`  
**Audit date:** 2026-09-05  
**Audit type:** Independent static source audit against the agreed MSSQL Database Discovery Tool specification.

> Important limitation: this audit read the current GitHub source and implementation artifacts. It did not execute the project's test suite or connect to the user's SQL Server from this environment. Repository-authored implementation/audit reports were treated as supporting evidence, not as independent proof.

---

## 1. Executive conclusion

The project is **real and substantially implemented**. It is not merely a scaffold.

Strongly implemented areas include:

- root `main.py`
- Windows launchers
- generic `.env` database configuration
- one- and multi-database operation
- sequential multi-database execution
- strict read-only ODBC connection intent
- fail-closed SQL safety validation
- broad SQL Server metadata inventory
- programmable object definition capture
- dependency/static-lineage analysis
- data profiling with thresholds
- PII/credential masking architecture
- explicit Git-safe export
- localhost Flask dashboard
- controlled HTML-triggered execution
- output/Git Export file browser
- Markdown/CSV/JSON/text/SQL/HTML renderers
- two- and three-run comparison
- numeric deltas and definition diffs
- extensive automated test source

However, the implementation is **not yet fully compliant with the comprehensive tool we specified**.

The most important remaining issues are:

1. PII detection can miss abbreviated/legacy School ERP column names, making Git sample export unsafe.
2. Controlled samples are not actually generated for all views and large tables.
3. `safe-profile` and `full-readonly` are effectively the same pipeline depth.
4. SQL Agent pipeline analysis captures a command hash, not the command logic/references, so scheduled pipeline lineage is incomplete.
5. Most discovery/profiling/lineage/reporting code is concentrated in one very large `fullrun.py`; the expected domain packages are mostly marker modules.
6. Every complete live discovery run invokes the project's pytest suite as stage 21, coupling production discovery to development/test source.
7. Exported comparison HTML is script-driven while the internal safe HTML renderer strips scripts, so browsing that exported HTML through the tool can render an empty comparison body.
8. Three-run top-level statuses/filters can hide secondary timeline events.
9. Comparison summary totals omit some comparison categories.
10. Several important SQL Server metadata families needed for a truly "whole database" catalogue are not yet inventoried.

Recommended disposition:

**Do not declare the MSSQL tool finished/frozen yet.**
Perform one focused remediation phase, then rerun static tests, live one-database validation, live second-database validation, Git-export safety checks, and 3-run UI comparison.

---

# 2. Requirement-by-requirement status

| Requirement | Status | Notes |
|---|---|---|
| Root main file | PASS | `main.py` exists and defaults to Web UI |
| CLI mode | PASS | metadata / metadata+logic / safe-profile / full-readonly exposed |
| Generic `.env` DB selection | PASS | single or multiple DBs |
| Sequential multi-DB | PASS | `run_all()` iterates configured DBs serially |
| Strict DB read-only | PASS | `ApplicationIntent=ReadOnly`, guarded SELECT-only cursor |
| No SP execution | PASS | definitions inspected statically |
| No Agent job execution | PASS | metadata only |
| Lazy `output/` | PASS | created only by real run |
| Lazy `git_export/` | PASS | explicit action only |
| Output/Git Export absent from repo | PASS | ignored and not committed |
| HTML dashboard | PASS | Flask loopback app |
| Execute discovery via HTML | PASS | predefined APIs; no arbitrary shell/SQL |
| Web CSRF/same-origin/Host safety | PASS | implemented |
| File browser | PASS | dual-root, containment checks |
| Markdown formatting | PASS | safe Markdown renderer |
| CSV formatting | PASS | pagination/search/sort |
| JSON formatting | PASS | pretty/large-file fallback |
| SQL/text formatting | PASS | paginated text/code presentation |
| Raw/full evidence retained | PASS | raw/download routes |
| 2-run comparison | PASS | implemented |
| 3-run comparison | PASS with issues | core comparison works; timeline filtering has edge cases |
| Definition diff | PASS | A-B / B-C / A-C unified diff |
| Whole table metadata | STRONG PARTIAL | broad but not exhaustive SQL Server metadata |
| Views | PARTIAL | metadata/definitions yes; sample data effectively skipped |
| Stored procedures | PASS/PARTIAL | metadata/definition/static refs; dynamic SQL limited |
| Functions | PASS/PARTIAL | static only, as intended |
| Triggers | PASS/PARTIAL | static only, as intended |
| SQL Agent pipeline detail | PARTIAL | command is hashed; lineage into command content unavailable |
| Sample each table/view | FAIL/PARTIAL | views and tables over safety threshold are skipped |
| Sensitive sample protection | PARTIAL / HIGH RISK | good framework, weak legacy-name detection |
| Data size/shape | PASS | table physical size + estimated rows |
| Inferred relationships | PASS/PARTIAL | heuristic and data validation present |
| Cardinality/orphans | PASS/PARTIAL | composite relationships not deeply validated |
| Column lineage | PARTIAL | useful static heuristics, not complete parser-level lineage |
| Pipeline lineage | PARTIAL | useful candidate discovery; SQL Agent command path incomplete |
| Per-object documentation | PASS | table and programmable docs generated |
| Styled static HTML report | PARTIAL | summary/navigation rather than full evidence portal; local UI carries full browsing |
| Git-safe export | STRONG PARTIAL | explicit audit, but depends on correct sensitivity classification |
| Modular architecture | FAIL/PARTIAL | `fullrun.py` is a large monolith |
| CI | NOT PRESENT | no `.github/workflows` found |
| Runtime self-test separation | FAIL | full discovery executes pytest as stage 21 |

---

# 3. Strong implementation findings

## 3.1 Entry point

`main.py` is a real root launcher.

It supports:

- default Web UI
- explicit `web`
- `test-connection`
- controlled CLI modes

This directly fixes the earlier missing-main issue.

## 3.2 Lazy evidence lifecycle

`inventory._new_run_directory()` creates only a real timestamped run directory after the user launches a real discovery workflow.

`output/` and `git_export/` are ignored by Git and are not present in repository contents.

Git export is created only via explicit exporter action.

This correctly fixes the earlier premature folder-generation problem.

## 3.3 Database read-only controls

The ODBC string includes:

`ApplicationIntent=ReadOnly`

The connection uses:

`autocommit=False`

and always performs rollback/close.

Every exposed cursor `.execute()` call goes through `validate_read_only_sql()`.

The validator restricts execution to SELECT / WITH...SELECT and blocks DML, DDL, EXEC/EXECUTE, administrative commands, `NEXT VALUE FOR`, OPENQUERY/OPENROWSET/OPENDATASOURCE and multiple statements.

This is one of the strongest parts of the project.

## 3.4 Web execution model

The browser does not execute Python directly.

It runs through a Flask service bound to loopback.

State-changing HTTP actions require same-origin + CSRF.

The API exposes only predefined discovery actions.

No arbitrary SQL endpoint and no arbitrary shell endpoint were identified in the inspected source.

## 3.5 File browsing and presentation

The browser implementation includes:

- Output root
- Git Export root
- breadcrumbs
- file listing
- search
- type metadata
- raw access
- download
- Markdown render
- CSV render with pagination
- JSON render
- text/SQL render
- generated HTML sanitization
- large-file safeguards

Path traversal and symlink escape protections are implemented.

## 3.6 Comparison

A real comparison package exists.

It supports exactly:

- 2 runs
- 3 runs

and calculates:

- A → B
- B → C
- A → C

It compares structural, metadata, code-definition, profiling, lineage, pipeline, risk and error artifacts.

Stored procedure/view/function/trigger definition differences include unified diffs.

This satisfies the main three-run comparison requirement.

---

# 4. Critical and high-priority gaps

## P0 — Sensitive data detection is not sufficiently safe for legacy School ERP schemas

### Location

`src/mssql_database_documenter/fullrun.py`

Sensitivity is primarily classified from regexes over column names and extended properties.

Current PII patterns include words such as:

- email
- phone
- mobile
- address
- dob
- father
- mother
- guardian
- name

### Problem

Legacy school databases frequently use abbreviations such as:

- `StudNm`
- `SName`
- `FName`
- `MName`
- `MobNo`
- `PhNo`
- `Addr1`
- `ResAdd`
- `PAddr`
- `BDate`
- `BirthDt`
- `ContactNo`

Some of these will not match the current detector.

Columns classified `Unknown` are preserved in samples.

The independent evidence audit validates whether *classified sensitive fields* are masked, but it does not magically identify a sensitive field that the classifier missed.

### Impact

If a missed field contains production student/parent data:

1. raw sample value can be written to `output`;
2. evidence audit may accept it;
3. Git Export may copy it;
4. the Git repository is public;
5. student/parent PII could be exposed.

### Required remediation

Add:

1. configurable sensitivity overrides file, e.g. `config/sensitivity_overrides.yaml`;
2. include/exclude rules by database/schema/table/column;
3. a School/legacy abbreviation dictionary;
4. content-based detectors for obvious emails/phones/etc. in sample values;
5. fail-safe Git-export policy:
   - either exclude samples by default from Git,
   - or mask all unknown string-like sample values unless explicitly allowlisted;
6. explicit pre-export report of every unmasked sample column.

Until this is repaired, **do not push production sample data into the public Git repository**.

---

## P1 — Sample data is not generated for all views

### Location

`SequentialRun.prompt08_samples()`

It builds `columns_by_object` for tables and views.

Before sampling, it calls the table-size threshold helper.

Views have no row in `TABLE_SIZE_PROFILE`, because physical table-size metadata applies to user tables.

Therefore the view's estimated row count is unavailable and the sample is emitted as header-only / skipped.

### Requirement conflict

The agreed tool must obtain controlled sample output for each accessible table and view.

### Required remediation

Implement separate view sampling policy:

```sql
SELECT TOP (@N) ...
FROM [schema].[view]
```

with:

- query timeout
- no expensive random ordering
- optional deterministic ordering when a suitable output column can be selected
- masking
- per-view skip/error logging
- configurable view-sampling enable/disable

Do not require table-size metadata for a view sample.

---

## P1 — Large tables are not sampled

The same safety threshold blocks sample extraction for any table exceeding `PROFILE_LARGE_TABLE_THRESHOLD`.

This is unnecessarily strict.

Deep profiling may be skipped for a million-row table, but a controlled `TOP 100` sample does not inherently require scanning the entire dataset when an appropriate access path exists.

### Required remediation

Separate:

- `PROFILE_LARGE_TABLES`
- `SAMPLE_LARGE_TABLES`

Large-table sample should normally remain enabled, with a conservative timeout and deterministic key ordering.

---

## P1 — `safe-profile` and `full-readonly` do not have distinct profiling depth

In `SequentialRun.run()`:

```text
profile_enabled = discovery_mode in {safe-profile, full-readonly}
```

Both modes then execute the same profiling and sample functions using the same thresholds.

There is no meaningful deeper full-readonly branch in the inspected run pipeline.

### Impact

The dashboard presents two different modes whose data-collection behavior is effectively the same.

### Required remediation

Define explicit semantics.

Example:

**safe-profile**
- metadata row estimates
- limited distinct
- low threshold
- TOP N samples
- declared relationships
- no expensive exact scan

**full-readonly**
- optional exact counts within explicit larger threshold
- deeper column profiles
- configurable relationship validation
- optional larger-table profiles
- view samples
- extended low-cardinality profiling

The mode difference must be visible in manifest/configuration.

---

## P1 — SQL Agent pipeline lineage is too shallow

### Location

`programmable_queries.SQL_AGENT_QUERY`

The query stores:

- job
- step
- subsystem
- database
- schedule
- SHA256 of `js.command`

but not the sanitized command text.

### Problem

Because only the hash is captured, the tool cannot statically determine whether a job step invokes:

- a stored procedure
- SSIS
- PowerShell
- CmdExec
- an import/export
- a table load
- another database
- a linked server

The pipeline catalogue consequently knows that a job/step exists but not its real lineage.

### Required remediation

Capture `js.command` into an internal analysis stream, sanitize it before persistence, and parse it according to subsystem.

For Git evidence:
- store sanitized command only where safe,
- or store extracted object references + command hash.

For SQL Agent T-SQL steps, identify static object references.

For SSIS/CmdExec/PowerShell steps, record sanitized invocation metadata and classify as external/opaque when necessary.

---

## P1 — Architecture is highly monolithic

The expected modular domains exist as package names, but many are marker modules only:

- `metadata/__init__.py`
- `profiling/__init__.py`
- `relationships/__init__.py`
- `lineage/__init__.py`
- `analysis/__init__.py`
- `reporting/__init__.py`

Most substantive work resides in:

`src/mssql_database_documenter/fullrun.py`

which handles:

- sensitivity classification
- profiling
- sampling
- relationship inference
- cardinality
- orphans
- lineage
- pipelines
- classification
- risk
- documentation
- diagrams
- HTML
- contract generation
- test execution
- manifests

### Impact

This makes future MariaDB support, testing, reuse and maintenance much harder.

### Required remediation

Refactor before using this as the shared database-documentation platform.

Suggested separation:

```text
profiling/
  column_profiler.py
  sampler.py
  sensitivity.py
  table_size.py

relationships/
  declared.py
  inference.py
  cardinality.py
  orphan.py

lineage/
  sql_parser.py
  dependency.py
  column_lineage.py
  pipeline.py
  external.py

analysis/
  classification.py
  duplicates.py
  risk.py
  data_quality.py

reporting/
  object_docs.py
  diagrams.py
  narratives.py
  html_report.py
  manifest.py
```

`fullrun.py` should become an orchestrator, not the domain implementation.

---

# 5. Medium-priority implementation issues

## P1/P2 — Full live discovery runs pytest as stage 21

`prompt21_review()` executes:

```text
python -m pytest -q
```

during every complete database discovery run.

This is not a database discovery concern.

### Problems

- production discovery is coupled to developer tests;
- a test failure can mark an otherwise valid DB evidence run as failed;
- package installations without test extras can fail;
- installed wheel/source layout may not contain the test tree expected by this stage;
- repeated DB runs waste time rerunning code unit tests.

### Recommendation

Move self-test to:

```text
python main.py self-test
```

and optionally run it as preflight.

Manifest should record last self-test version/result, but a database evidence run should not invoke pytest internally.

---

## P1 — Exported comparison HTML conflicts with safe HTML rendering

`comparison/exporters.py` generates an HTML file where JavaScript parses embedded JSON and populates a `<pre>`.

`web/renderers.py` intentionally removes `<script>` from trusted HTML.

Therefore, when that exported comparison HTML is opened **inside the local evidence browser**, the script is removed and the content container can be empty.

### Recommendation

Generate static HTML on the server.

Do not rely on inline JavaScript to materialize the exported comparison.

The exported HTML should include already-rendered:

- run metadata
- summary cards
- category navigation
- comparison tables
- numeric deltas
- definition diffs

and remain safe after sanitization.

---

## P2 — Comparison export HTML is not sufficiently presentable

Even when opened directly, current export primarily pretty-prints the entire comparison JSON in `<pre>`.

That preserves data, but it is not the polished comparison report originally requested.

Use structured tables and collapsible detail sections.

---

## P2 — Three-run top status can hide secondary events

Example:

```text
Run A: object absent
Run B: object added
Run C: object changed
```

Timeline events include:

- `ADDED_IN_B`
- `CHANGED_B_TO_C`

but the top-level status prioritizes one event.

The HTML filters operate largely on the top status, so "Changed only" can miss an object that was added and then changed.

### Recommendation

Filters should evaluate `timeline_events`, not just `status`.

The UI can display multiple timeline badges.

---

## P2 — Comparison summary totals are incomplete

`comparison.engine.compare_run_paths()` builds summary totals while iterating the main `CATALOGUES`.

Additional categories are added afterward:

- database_summary
- data_types
- definition_hashes
- data_quality
- coverage

Their statuses do not contribute to the top summary counts.

Detailed categories still exist, but summary numbers can be misleading.

---

## P2 — "Reports" action performs a fresh full DB run

The Web `reports` action routes back to `run_all()`.

That does not simply regenerate styled documentation for an existing run.

### Recommendation

Either:

1. rename it to `Run Discovery + Reports`, or
2. implement `Regenerate Reports` for a selected manifested run without reopening the DB.

---

# 6. Metadata completeness gaps

The current metadata catalogue is broad but should not yet be called a complete SQL Server inventory.

Important families not identified in the current query registry include:

- database files and filegroups
- database-level storage allocation
- partition functions
- partition schemes
- partition-level compression
- user-defined alias/table types
- statistics metadata
- full-text indexes/catalogues
- change tracking configuration
- CDC configuration
- database principals/roles/permissions, if approved and safely sanitized
- Service Broker objects, if relevant
- XML schema collections
- database-scoped configurations

Not every obscure SQL Server feature must be mandatory, but the tool should at least:

1. inventory whether these feature families are present;
2. document supported/unsupported status;
3. capture them when visible and safe.

---

# 7. Relationship/lineage limitations

The relationship implementation is useful and correctly separates declared and inferred evidence.

However:

- composite FK data validation is deliberately skipped per-column;
- inferred relationship candidates are restricted to identifier-like names;
- only top few scored candidates are retained;
- static SQL lineage is regex/alias-based, not full T-SQL AST lineage;
- dynamic SQL is necessarily opaque.

These limitations are acceptable if documented, but they mean lineage is **comprehensive best-effort**, not mathematically complete.

---

# 8. Testing and verification

The repository contains extensive tests for:

- CLI
- config
- connection
- SQL safety
- evidence safety
- inventory
- full run
- comparison
- file browser
- job manager
- renderers
- Web app

The repository's own implementation report states that live read-only discovery completed on two SchoolERP databases and that the automated tests passed.

This independent audit did not execute those tests or connect to the DB, so that claim should remain "repository-reported" until reproduced externally.

No GitHub Actions workflow was found in the repository, so current test execution is local rather than independently enforced by CI.

Recommended addition:

```text
.github/workflows/test.yml
```

running offline/unit tests on push/PR.

Live MSSQL integration tests should remain separately controlled.

---

# 9. Recommended remediation order

## Gate A — before committing any production samples

1. Strengthen sensitivity classification.
2. Add database/schema/table/column override configuration.
3. Default Git export to exclude unknown-string sample values or mask them.
4. Test against real legacy column names.
5. Re-run evidence safety.

## Gate B — completeness

6. Add view samples.
7. Add large-table TOP N sample path.
8. Differentiate safe-profile/full-readonly.
9. Expand SQL Agent job static lineage.
10. Add missing SQL Server metadata families.

## Gate C — architecture

11. Decompose `fullrun.py`.
12. Move pytest/self-test out of live discovery.
13. Add CI.

## Gate D — comparison/presentation

14. Fix timeline-event filtering.
15. Fix summary totals.
16. Generate static, styled comparison HTML.
17. Separate "report regeneration" from DB discovery.

---

# 10. Final assessment

### Overall

**Substantially implemented: YES.**

**Implemented exactly as discussed: NO, not yet.**

### Rough readiness

| Area | Readiness |
|---|---:|
| Read-only safety | 95% |
| Entry/CLI/Web orchestration | 95% |
| Output lifecycle | 95% |
| HTML file browser | 90% |
| 2/3-run comparison | 85% |
| Generic schema inventory | 85% |
| Profiling | 75% |
| Sample coverage | 60% |
| PII-safe Git sample export | 65% until legacy detector hardened |
| Pipeline lineage | 65% |
| Modular maintainability | 50% |
| Whole-SQL-Server metadata completeness | 70% |
| Overall tool readiness | ~80% |

The strongest recommendation is to perform a focused **v3.1 remediation** rather than rebuild the project. Preserve the strong entry point, SQL safety, Web UI, browser, run registry, comparison core, evidence contracts and Git-export architecture; repair the gaps above.
