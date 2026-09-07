# Prompt 07 — MSSQL Metadata Completeness

## Objective
Expand to a defensible whole-database catalogue.

Add safe registered SELECT metadata families for at least:
1. database files
2. filegroups
3. partition functions
4. partition schemes
5. partition/compression metadata
6. user-defined alias/table types
7. statistics metadata
8. full-text catalog/index metadata
9. CDC status
10. Change Tracking status
11. database-scoped configurations
12. XML schema collections

Optional security metadata must be explicitly enabled and sanitized.

Every family requires QuerySpec, explicit columns, output artifact, contract/capability matrix, absent/inaccessible state, comparison category where meaningful, SQL-safety test. Add feature-support overview with present/absent/inaccessible/unsupported. No silent omissions.

STOP.
