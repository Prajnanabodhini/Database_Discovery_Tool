# MASTER REMEDIATION PROMPT — MSSQL Database Discovery Tool v3.1

You are repairing repository `Prajnanabodhini/Database_Discovery_Tool`. The independently audited baseline is `1c608d12d7c0f107931144dbbdc4e536865ab546`.

Your task is to create a production-safe **v3.1** by fixing the audit findings while preserving all correct v3 behavior.

# 1. Non-negotiable operating rules

## Do not rebuild
Refactor/repair existing code. Preserve interfaces unless this prompt explicitly changes them.

## Git safety
Before changes run `git status --short`, `git rev-parse HEAD`, `git branch --show-current`. If user changes exist, preserve them. Never reset/clean/overwrite them. If HEAD differs from `1c608d12d7c0f107931144dbbdc4e536865ab546`, inspect the diff first. No force-push/history rewrite. Never commit `.env`, credentials, `output/`, `git_export/`, real samples, logs, caches, `.venv` or build products.

## Database safety
The tool must remain strictly read-only. Never add DML/DDL/admin execution, discovered-procedure execution, Agent execution, arbitrary SQL or shell endpoints. Keep `ReadOnlyCursor`, fail-closed SELECT validation, `ApplicationIntent=ReadOnly`, timeout, autocommit disabled and rollback/close. Every new SQL Server query must be a registered static SELECT and pass `validate_read_only_sql`.

## Runtime evidence
Import/install/tests/Web startup/dry-run/self-test must not create `output/` or `git_export/`. A real discovery may create `output/<db>/run_*`; only explicit Git export may create `git_export/`. Never mutate historical evidence.

## Live DB authorization gate
Do not run live MSSQL discovery until all offline gates pass and the operator explicitly authorizes it. When authorized, validate one DB at a time: dry-run → connection test → metadata → inspect → metadata+logic → inspect → safe-profile → inspect → full-readonly only if approved.

# 2. Required fixes

## P0 — Legacy sensitive fields and Git export
Extract sensitivity logic into a real profiling/sensitivity module. Return `category`, `action`, `confidence`, `evidence`. Layer classification: configurable overrides → conservative built-in modern/legacy names → extended properties → safe value-pattern signals. Recognize legacy school abbreviations including `StudNm`, `StudName`, `SName`, `FName`, `MName`, `FatherNm`, `MotherNm`, `GuardianNm`, `MobNo`, `MobileNo`, `PhNo`, `PhoneNo`, `ContactNo`, `Addr1`, `Addr2`, `ResAdd`, `PAddr`, `DOB`, `BDate`, `BirthDt`, Aadhaar/Aadhar, PAN, passport and email variants.

Create dependency-light config such as `config/sensitivity_overrides.toml.example` using Python 3.11 `tomllib`. Support exact/pattern rules with documented precedence.

Git export must not rely on perfect classification. Add `GIT_EXPORT_SAMPLE_POLICY=exclude|masked_only`, default `exclude`, and **no raw mode**. `exclude` omits sample payload CSVs but retains indexes/masking/sensitivity reports. `masked_only` performs a second export-time sanitization without mutating source run. Export checklist/manifest must state policy. Tests must prove raw synthetic legacy PII cannot reach Git export.

## P1 — View samples
Current view samples are skipped because table-size estimates are required. Separate view sample policy. For accessible views, attempt controlled `SELECT TOP (N) ... FROM [schema].[view]` with timeout, no random sort, no size-estimate prerequisite, masking before disk, explicit skip/error status. Add settings `SAMPLE_TABLES`, `SAMPLE_VIEWS`, `SAMPLE_ROW_LIMIT` (backward compatibility allowed).

## P1 — Large-table samples
Deep profiling and sampling must use separate eligibility. Large tables may get conservative TOP-N samples even when deep profile is skipped. Prefer cheap PK/unique ordering; otherwise TOP-N without expensive sort. Never exact-count merely to decide sampling; never `ORDER BY NEWID()` or `TABLESAMPLE`. Add `SAMPLE_LARGE_TABLES=true` and record ordering/sample status.

## P1 — Truthful discovery modes
Replace scattered booleans with a resolved mode policy object/dataclass. Define:
- `metadata`: structural catalog only;
- `metadata+logic`: metadata + programmable definitions/static dependencies/pipelines;
- `safe-profile`: conservative bounded data validation/samples/profiles/relationship checks;
- `full-readonly`: deeper explicitly configured read-only analysis with larger limits/optional exact counts within hard ceilings/deeper distributions/relationship validation.
Persist resolved policy in run config/summary/manifest. Tests must prove safe-profile and full-readonly take different branches.

## P1 — SQL Agent pipeline lineage
Do not execute commands. Make Agent command text available only to sanitizer/static parser. Persist command SHA and safe derived references; optionally sanitized command if provably safe. For TSQL extract conservative READ/WRITE/CALL/database/external references and dynamic-SQL opacity. For SSIS/PowerShell/CmdExec/etc record sanitized invocation hints and opaque/external classification. Add `SQL_AGENT_STEP_REFERENCES.csv` and `SQL_AGENT_PIPELINE_EDGES.csv`; merge safe edges into pipeline/lineage with evidence classes. Test fake secrets never persist.

## P1 — MSSQL metadata completeness
Add registered SELECT catalogues for: database files, filegroups, partition functions, partition schemes, partition/compression metadata, user-defined alias/table types, statistics, full-text metadata, CDC status, Change Tracking status, database-scoped configurations, XML schema collections. Optional security metadata must be explicitly enabled and sanitized. Each family needs QuerySpec, typed output, contract, capability matrix, meaningful comparison category, absent/inaccessible handling and SQL-safety test. Add a support overview: present/absent/inaccessible/unsupported.

## P1 — Modularize `fullrun.py`
Refactor, do not rewrite. Move domain logic into real modules under profiling, relationships, lineage, analysis, reporting. `fullrun.py` should mainly own run state, stage sequencing, cancellation/error recording, connection lifecycle and domain orchestration. Preserve APIs/compatibility imports. Add characterization tests before each extraction; avoid circular imports.

Suggested ownership:
```text
profiling/sensitivity.py
profiling/sampler.py
profiling/column_profiler.py
relationships/inference.py
relationships/cardinality.py
relationships/validation.py
lineage/static_sql.py
lineage/dependencies.py
lineage/agent.py
lineage/pipeline.py
analysis/classification.py
analysis/duplicates.py
analysis/quality.py
analysis/risk.py
reporting/object_docs.py
reporting/diagrams.py
reporting/narratives.py
reporting/html_report.py
reporting/manifests.py
```

## P1 — Remove pytest from live discovery
Runtime stage 21 must not run `python -m pytest`. Retain lightweight current-run semantic invariants. Add `python main.py self-test` as offline developer/operator check; optional Web self-test is allowed if offline/lazy/sanitized. Discovery must work even if pytest/test source is unavailable. Tests: live-run path never invokes pytest; self-test may use fixed argv; self-test does not connect or create runtime evidence.

## P1/P2 — Comparison/export
Replace script-dependent comparison HTML with static server-rendered safe HTML containing run metadata, warnings, summary, category sections, A/B/C, A→B/B→C/A→C, timeline events, numeric deltas, definitions/diffs. It must remain useful after all scripts are removed.

Three-run filtering must evaluate `timeline_events`/interval statuses, not only one priority status. Example absent→added→changed must match both Added and Changed filters. Summary totals must include all displayed categories or clearly state a narrower scope. HTML must be human-readable; JSON/CSV remain canonical machine outputs.

## P2 — Reports action
Stop advertising a "reports" action that starts a fresh DB run. Preferred: add `regenerate-reports` for one manifested run, local-only, no MSSQL connection and no canonical evidence mutation. If full regeneration is impractical, remove/rename the misleading action. Test local regeneration never calls `connect()`.

## P2 — CI
Add `.github/workflows/test.yml` for offline compile/import + pytest and assert repository output/git-export roots are not created. No live DB and no production secrets. Prefer Windows operator parity.

# 3. Mandatory regression tests

Add tests for: legacy PII classification/overrides/value signals; Git export sample exclusion/masked-only; view sampling without size estimate; large-table sampling independent of profile; safe-profile/full-readonly branch differences; Agent commands never execute and refs extract; every new metadata query passes SQL validator; modular orchestrator behavior; runtime stage 21 no pytest; `main.py self-test` offline/lazy; static comparison HTML no script dependency; multi-event 3-run filters; truthful comparison totals; report regeneration no DB; import/Web/help/dry-run laziness; no arbitrary SQL/shell; path/symlink guards; Git exporter fail-closed.

# 4. Documentation

Update README, SAFETY_MODEL, OPERATOR_RUN_GUIDE, HTML help, runtime-output contract, `.env.example`, config README, implementation report and final file audit. Explicitly document mode differences, Git sample policy, metadata coverage and historical-output safety caveat.

# 5. Required report

Create `V3_1_REMEDIATION_REPORT.md` with starting SHA, ending state, files changed, finding→fix matrix, tests/results, static SQL count, lazy lifecycle checks, privacy/comparison gates, CI, live validation only if actually authorized/executed, unresolved limits and exact commands.

# 6. Completion response

Return a matrix `Finding | Files changed | Tests | Result`, offline suite result, compile/import result, whether live DB was touched, runtime evidence created, Git export generated and unresolved limitations. Do not claim PASS while any P0/P1 remains unresolved.
