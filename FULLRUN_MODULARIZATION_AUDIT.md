# `fullrun.py` Modularization Audit

Recorded: 2026-09-06  
Scope: Prompt 08 only  
Execution boundary: offline; no MSSQL connection, discovery run, Git export, or historical-evidence write

## Result

`SequentialRun` remains the public sequential engine, but domain behavior is now supplied
by one-way mixins. `fullrun.py` was reduced from 1,677 to 364 lines (1,313 lines / 78.3%).
It retains run state, sequential stage gates, cancellation/error handling, connection and
cursor lifecycle, core metadata acquisition, the safety stages, and orchestration.

## Ownership

| Owner | Lines | Responsibility |
|---|---:|---|
| `fullrun.py` | 364 | Run state, stage gates, cancellation/errors, connection lifecycle, core metadata, safety stages, orchestration |
| `runtime.py` | 78 | Shared serialization, identifiers, object keys, access-error classification, SQL-safety adapter |
| `profiling/policy.py` | 37 | Type families, sensitivity classifications, deterministic masking policy |
| `profiling/stages.py` | 323 | Size/shape, profiling, sampling, sensitivity stages |
| `relationships/inference.py` | 9 | Relationship identifier normalization |
| `relationships/stages.py` | 131 | FK/inferred relationships, cardinality, validation, orphan analysis |
| `lineage/static_sql.py` | 136 | Sanitized static definitions and object/column reference inference |
| `lineage/stages.py` | 259 | Programmable catalogues, lineage, cross-database references, SQL Agent and pipelines |
| `analysis/stages.py` | 127 | Structural classification, duplicate candidates, data quality, risk register |
| `reporting/stages.py` | 415 | Object docs, diagrams, narratives, HTML, acceptance, control files, manifests |

The generated `FINAL_CODE_REVIEW.md` now includes this same ownership boundary and
resolves control-check locations in the extracted modules.

## Dependency and compatibility audit

- Domain stage modules do not import `fullrun`; dependency direction is one way from
  the orchestrator to domain modules.
- `SequentialRun` inherits the five domain mixins, so the existing stage method surface
  remains callable without caller changes.
- Former module-level helper imports remain available from `fullrun.py` as compatibility
  aliases while their implementations have explicit domain owners.
- `_programmable_headers` remains a static method after extraction.
- Reporting self-review resolves the installed runtime package root without requiring
  pytest or test source and locates masking, required-output, and manifest checks at
  their current owners.
- `safety.py` and `connection.py` were not changed by Prompt 08. Registered SQL remains
  covered by the fail-closed validation suite, and execution still uses `ReadOnlyCursor`.

## Characterization and regression evidence

Characterization tests were added and passed before any extraction. They freeze the
public stage surface, static-analysis helper behavior, pipeline evidence/header contract,
and narrative/control-file content.

| Gate | Result |
|---|---|
| Pre-extraction characterization baseline | `4 passed` |
| Helper compatibility gate | `23 passed, 70 subtests passed` |
| Profiling extraction gate | `43 passed, 85 subtests passed` |
| Relationship extraction gate | `30 passed, 72 subtests passed` |
| Lineage extraction gate after caught decorator repair | `34 passed, 70 subtests passed` |
| Analysis extraction gate | `30 passed, 72 subtests passed` |
| Reporting extraction gate | `27 passed, 70 subtests passed` |
| Modular ownership/characterization gate | `38 passed, 93 subtests passed` |
| Final full offline regression suite | `141 passed, 2 skipped, 197 subtests passed` |
| Python source/test compile audit | PASS; 70 files |
| `git diff --check` | PASS; informational Windows LF/CRLF notices only |

The lineage gate initially failed because the mechanical move did not include the
`@staticmethod` decorator on `_programmable_headers`. The gate prevented progression;
the decorator was restored, the orphan decorator was removed from `fullrun.py`, and the
same gate then passed.

## Output and safety contract

- No intended artifact name, folder, CSV header, JSON shape, narrative wording, stage
  number, or stage order changed during extraction.
- Historical `output/`: 2,311 files / 27,547,593 bytes.
- Historical `git_export/`: 2,311 files / 27,547,593 bytes.
- Combined historical evidence: 4,622 files / 55,095,186 bytes, matching the established
  remediation baseline.
- No live MSSQL connection was attempted and no live SQL was executed.
- The two full-suite skips are the pre-existing Windows symbolic-link privilege cases.

## Files added for Prompt 08

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

## Final gate

All Prompt 08 acceptance gates passed. Prompt 09 is outside this audit and was not read
or started.
