# MASTER PROMPT — Generic MSSQL Database Discovery, Profiling, Lineage & Documentation Engine

Build a reusable Windows-friendly Python 3.11+ project named `mssql_database_documenter`. It must connect to whichever Microsoft SQL Server database(s) are configured in `.env` and produce comprehensive read-only technical documentation of the entire accessible database. The implementation must be generic and must not hardcode Student/SchoolERP-specific tables, schemas, IDs, or business domains.

## Objectives
Document end to end: server/database metadata; schemas; tables; columns; PKs; FKs; unique/check/default constraints; indexes; relationships; inferred relationships; cardinality; orphan relationships; table sizes; row counts; table/column shape; safe masked sample data; views; stored procedures; functions; triggers; synonyms; sequences; computed columns; extended properties; object dependencies; column lineage where feasible; cross-database/cross-server references; SQL Server Agent job metadata when visible; potential pipelines; static database-side business logic; data-quality characteristics; lookup/master/transaction/bridge/history candidates; duplicate/parallel structures; risks; uncertainties; discovery coverage; access limitations; machine-readable catalogues; human-readable docs; and a sanitized Git-safe export.

## Multi-database configuration
Support either `MSSQL_DATABASE=DatabaseA` or `MSSQL_DATABASES=DatabaseA,DatabaseB`. Process configured DBs sequentially and isolate output under `output/<database>/run_YYYYMMDD_HHMMSS/`. Never automatically scan all server DBs. Every evidence row should include server/database/schema/object context. Support `--database` CLI override. Optionally generate a cross-database comparison without merging data. Never assume equal IDs in two DBs mean equal business values.

## Environment variables
Support MSSQL_SERVER, MSSQL_DATABASE, MSSQL_DATABASES, MSSQL_DRIVER, MSSQL_TRUSTED_CONNECTION, MSSQL_USERNAME, MSSQL_PASSWORD, MSSQL_ENCRYPT, MSSQL_TRUST_SERVER_CERTIFICATE, MSSQL_QUERY_TIMEOUT_SECONDS, DISCOVERY_MODE, PROFILE_SAMPLE_ROWS, PROFILE_INCLUDE_SAMPLE_DATA, PROFILE_MASK_SENSITIVE_DATA, PROFILE_EXACT_ROW_COUNTS, PROFILE_DISTINCT_VALUES, PROFILE_MAX_DISTINCT_VALUES, PROFILE_LARGE_TABLE_THRESHOLD, DISCOVER_SQL_AGENT_JOBS, OUTPUT_ROOT, SANITIZE_SERVER_NAME. Secrets only in environment/local `.env`; `.env` must be gitignored.

## Absolute safety
STRICTLY READ ONLY. Never execute/implement INSERT, UPDATE, DELETE, MERGE, TRUNCATE, CREATE, ALTER, DROP, GRANT, REVOKE, DENY, BACKUP, RESTORE, EXEC/EXECUTE, mutating DBCC, job execution, trigger enable/disable, sequence NEXT VALUE, or DB/server configuration changes. Never execute stored procedures/functions/jobs to understand them. Inspect definitions statically. All project-owned SQL must pass a fail-closed guard permitting only SELECT, WITH...SELECT, safe catalog/INFORMATION_SCHEMA queries. Provide dry-run and tests.

## Suggested stack
Python 3.11+, pyodbc, python-dotenv, pandas, sqlparse, networkx, jinja2, pytest; standard library where practical. CLI only.

## Suggested structure
`src/mssql_database_documenter/` with modules for config, connection, safety, metadata, profiling, relationships, lineage, analysis, reporting; `sql/`; `tests/`; `output/`. Keep modules small/testable.

## CLI
Implement dry-run, test-connection, inventory, programmable-objects, profile, relationships, lineage, pipelines, report, all; support `--mode metadata|metadata+logic|safe-profile|full-readonly`. First production run should favor metadata+logic or safe-profile.

## Metadata
Capture server/version/edition/instance/collation/driver and database name/id/create date/compatibility/collation/state/recovery/read-only/snapshot/containment/page verification. Capture all schemas. For every table capture object metadata, estimated rows, column count, PK/FK/index/constraint counts, temporal/system-versioning, memory-optimized/filegroup if visible, and inferred structural category (Master/Transaction/Lookup/Bridge/History/Audit/Staging/Archive/Configuration/Unknown).

For every column capture ordinal/type/length/precision/scale/nullability/identity/computed/persisted/default/collation/sparse/rowguid plus inferred semantic and sensitivity categories. Capture PKs, FKs with referential actions/trust state, unique/check/default constraints, all indexes including keys/includes/filters/disabled state. Capture SQL Server extended properties such as MS_Description and prefer those over naming inference.

## Inferred relationships
Discover undeclared relationship candidates using names, compatible types, unique/index patterns, value-domain overlap, and joins found in views/procedures/functions/triggers. Where safe calculate source/target distincts, matched/unmatched/nulls/duplicate matches. Classify DECLARED_FK, DATA_VALIDATED, CODE_LOGIC_INFERRED, SCHEMA_INFERRED, LOW_CONFIDENCE. Never present inferred as declared. Determine likely 1:1, 1:N, N:1, N:N and optional relationships. Produce orphan analysis within safety thresholds.

## Size and shape
For every table retrieve estimated rows, reserved/used/data/index/unused space in KB/MB/GB. Rank largest tables. Capture rows, columns, type-family counts, identifiers, nullable/computed counts. Default to estimated row counts; exact COUNT(*) only if configured and within safe thresholds. Label EXACT vs ESTIMATED.

## Column profiling
Where suitable collect null/non-null, distinct %, min/max, safe avg/stddev, string lengths, date ranges, empty/whitespace, zero/negative counts, booleans, candidate uniqueness, all-null/constant. Skip expensive/meaningless blob/large text/encrypted metrics. For low-cardinality safe columns emit value/count/% up to configured limit; otherwise only distinct count. Respect large-table threshold and mark SKIPPED_FOR_SAFETY when needed.

## Samples
Generate controlled sample for every accessible table and view, default TOP N via deterministic strategy such as PK ordering. Avoid ORDER BY NEWID on large tables. Include headers and sampling metadata. Samples must pass sensitive-data detection/masking. Detect likely PII, credentials, financial, health, potentially sensitive fields. Default PROFILE_MASK_SENSITIVE_DATA=true. PII may be deterministically pseudonymized; credentials/passwords/hashes/tokens/secrets must always be `[REDACTED]`. Never execute procedures/triggers for samples.

## Programmable objects
Inventory all views, stored procedures, scalar/inline/multi-statement functions, triggers, synonyms, sequences, computed expressions, and SQL Agent jobs/steps/schedules if accessible. Capture metadata, parameters, definitions, normalized-definition SHA256, dependencies, likely reads/writes, nested calls, temp tables, dynamic SQL, transaction/error handling and possible business-rule logic. Detect EXEC(...), sp_executesql, concatenated dynamic SQL and mark DYNAMIC_SQL_PRESENT. Never execute these objects.

## Dependencies and lineage
Build object edge catalogues for View→Table/View, Procedure→Table/View/Procedure/Function, Function→Table/View/Function, Trigger→Table/View, Synonym→external, Agent Job→procedure/command. Record source/target server/database/schema/object/type, read/write/call/reference, evidence, confidence. Attempt column lineage and classify DIRECT/DERIVED/AGGREGATED/CONDITIONAL/UNKNOWN. Detect cross-database three-part names, cross-server four-part names, linked servers, OPENQUERY, synonyms; document but do not query external systems unless separately configured.

## Pipeline discovery
Build candidate flows like Source Table→View→Procedure→Destination or Job→Procedure→Staging→Trigger→Final. Capture origin/trigger, source, transformations, destination, schedule, read/write, external dependency, confidence. Classify CONFIRMED_DEPENDENCY, LIKELY_PIPELINE, POSSIBLE_PIPELINE, HISTORICAL_OR_UNKNOWN, DYNAMIC_SQL_OPAQUE. Object existence alone never proves active use.

## Structural analysis
Infer possible lookup/master/transaction/bridge/history/audit/staging/archive/config tables using structural evidence and label as inference. Detect duplicate/parallel structures using name similarity, column/key overlap, definition similarity, dependencies and row counts. Generate high-impact structural-centrality objects (many inbound/outbound refs), but call it structural centrality, not business criticality.

## Data quality and risks
Observe tables without PK, duplicate key candidates, nullable/orphan references, empty/whitespace strings, all-null/constant columns, odd date ranges, extreme numeric values, disabled/untrusted constraints, dynamic SQL, encrypted modules, external dependencies, stale-looking objects, sensitive-data exposure and permission limitations. Use Critical/High/Medium/Low/Informational cautiously. Generate ACCESS_AND_DISCOVERY_LIMITATIONS and never silently omit inaccessible categories.

## Output tree
Use `output/<DATABASE>/run_<timestamp>/` with folders: 00_Run_Metadata, 01_Executive_Summary, 02_Server_Database, 03_Schemas, 04_Tables, 05_Columns, 06_Keys_Relationships, 07_Indexes_Constraints, 08_Views, 09_Stored_Procedures, 10_Functions, 11_Triggers, 12_Synonyms_Sequences, 13_Data_Profiling, 14_Samples, 15_Lineage, 16_Pipelines, 17_Data_Quality, 18_Risks_Uncertainties, 19_Diagrams, 20_Object_Documentation, 99_Git_Handoff.

## Required outputs
At minimum: MSSQL_EXECUTIVE_SUMMARY.md, DATABASE_OVERVIEW.md, DATABASE_SUMMARY_METRICS.json, DATABASE_GLOSSARY.md, DISCOVERY_COVERAGE.md, DISCOVERY_ERRORS.csv, SCHEMA_CATALOGUE.csv, TABLE_CATALOGUE.csv, COLUMN_CATALOGUE.csv, PRIMARY_KEYS.csv, FOREIGN_KEYS.csv, INFERRED_RELATIONSHIPS.csv, RELATIONSHIP_CARDINALITY.csv, ORPHAN_ANALYSIS.csv, INDEX_CATALOGUE.csv, CONSTRAINT_CATALOGUE.csv, TABLE_SIZE_PROFILE.csv, TABLE_SHAPE_PROFILE.csv, COLUMN_PROFILE.csv, VIEW_CATALOGUE.csv, VIEW_DEPENDENCIES.csv, STORED_PROCEDURE_CATALOGUE.csv, STORED_PROCEDURE_DEPENDENCIES.csv, FUNCTION_CATALOGUE.csv, TRIGGER_CATALOGUE.csv, SYNONYM_CATALOGUE.csv, SEQUENCE_CATALOGUE.csv, EXTENDED_PROPERTIES.csv, OBJECT_DEPENDENCIES.csv, LINEAGE_EDGES.csv, LINEAGE_SUMMARY.md, PIPELINE_CATALOGUE.csv, PIPELINE_SUMMARY.md, DATA_QUALITY_SUMMARY.md, POSSIBLE_MASTER_TABLES.csv, POSSIBLE_LOOKUP_TABLES.csv, POSSIBLE_TRANSACTION_TABLES.csv, POSSIBLE_BRIDGE_TABLES.csv, POSSIBLE_HISTORY_AUDIT_TABLES.csv, POSSIBLE_DUPLICATE_OR_LEGACY_STRUCTURES.md, HIGH_IMPACT_OBJECTS.csv, RISK_AND_UNCERTAINTY_REGISTER.csv, ACCESS_AND_DISCOVERY_LIMITATIONS.md, manifest.json, checksums.sha256, SAFE_TO_COMMIT_CHECKLIST.md. If a category is absent/inaccessible, still create a file stating this.

## Per-object documentation
Generate Markdown for every table/view/procedure/function/trigger. Table docs include identity, inferred purpose, size/shape, columns, keys, inbound/outbound relations, indexes, constraints, references/referenced-by, profiles, masked samples, data-quality observations, lineage, pipeline participation, risks and uncertainties. Programmable-object docs include parameters, definition hash, reads/writes/calls, static logic, dynamic SQL/temp tables/transactions/error handling, pipeline role and uncertainties.

## Diagrams
Generate full ER Mermaid plus per-schema/cluster diagrams; dependency diagrams for views/procedures/functions/triggers/jobs/cross-db. Do not rely only on one giant unreadable graph.

## Repeatability
Every run creates a new timestamped folder and definition hashes. Design formats for future run-to-run diff: added/removed tables/columns/indexes, changed definitions, row growth, schema drift. Generate manifest with run ID/timestamp/tool/Python/packages/ODBC/SQL version/sanitized server/database/stages/warnings/files; generate SHA256 for every artifact. No secrets.

## Multi-database comparison
When multiple DBs are configured, optionally generate DATABASE_COMPARISON.md and CSV/JSON diffs for schemas/tables/columns/types/PK/FK/index/constraints/definition hashes/object counts/row counts/safe lookup values. Never merge DB data or assume ID equivalence.

## Git-safe export
Create `git_export/MSSQL/<DATABASE>/` containing only sanitized documentation/evidence. Exclude .env, credentials, raw unmasked PII, secret-bearing logs/connection strings, cache/temp files. Generate SAFE_TO_COMMIT_CHECKLIST.md.

## Performance safety
Profiling can consume resources despite read-only access. Avoid full scans/random sorts/distincts on huge fields/fragmentation scans/stat updates/plan forcing. Use thresholds, timeouts and reduced profiling mode. README must warn to start metadata-only and use low-usage periods for production profiling.

## Coverage and errors
Generate DISCOVERY_COVERAGE.md showing documented/profiled/sample counts and explanations for shortfalls. Generate DISCOVERY_ERRORS.csv with stage/object/error type/sanitized message/impact/continuation. Continue independent safe stages.

## Tests
Test SQL safety, secret redaction, PII detection/masking, config, output layout, CSV/JSON, definition hashes, relationship classification, dry-run, large-table behavior, multi-DB isolation and Git sanitization.

## Evidence language
Always separate FACT, DATA VALIDATION, INFERENCE, UNKNOWN. Never state semantic assumptions as facts.

## Completion gate
Do not claim completion until dry-run works; no mutation capability exists; all accessible metadata/programming objects are inventoried; sizes/shapes/safe samples/profile/relationships/lineage/pipelines/data quality/risks/coverage/errors/manifests/checksums/Git export are generated; tests pass. Final response must include project path/tree, Python/dependencies, `.env`, run commands, modes, output paths, test results, safeguards, limitations, Git-safe folder, and explicit confirmation that no DB mutation capability was implemented.
