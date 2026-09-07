# Prompt 04 — View and Large-Table Sample Coverage

## Objective
Retain controlled sample evidence for accessible tables/views without making deep profiling unsafe.

Refactor sampling into a dedicated sampler. Separate profiling eligibility from sampling eligibility.

### Tables
If enabled, attempt TOP-N even when table exceeds profile threshold. Prefer cheap PK/unique ordering; otherwise TOP-N without expensive order. Never exact-count to decide sampling. Never ORDER BY NEWID or TABLESAMPLE.

### Views
Views must not require table-size metadata. Attempt controlled `SELECT TOP (N) ... FROM [schema].[view]` with timeout and masking. Record inaccessible/slow/failing states explicitly.

### Settings
Normalize `SAMPLE_TABLES`, `SAMPLE_VIEWS`, `SAMPLE_LARGE_TABLES`, `SAMPLE_ROW_LIMIT` while preserving compatibility where practical.

### Sample index
Record object type, requested rows, returned rows, ordering strategy, status, masked-sensitive-column count.

### Tests
View/no-estimate still samples; large table above profile threshold samples; large table remains excluded from deep profile; sample SQL passes validator; no random/TABLESAMPLE; masking before disk.

STOP.
