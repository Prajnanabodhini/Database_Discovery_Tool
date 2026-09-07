# Prompt 13 — Authorized Live DB2 Read-Only Validation

## Preconditions

Run only after DB1 fully passes Prompt 12.

Use exactly one second explicitly configured database.

## Order

Repeat:

1. dry-run
2. test-connection
3. metadata
4. metadata+logic
5. safe-profile
6. evidence audit
7. Git-export safety check

## Purpose

This is not redundant.

DB2 validates that v3.1.1 changes are:
- generic;
- not SchoolERP-table-name dependent;
- not accidentally bound to DB1 lineage;
- stable across separate schemas/objects.

## Required checks

- no cross-DB contamination;
- output root isolated by database;
- manifest database identity correct;
- mode policy correct;
- external/opaque view skip rule generic;
- Git profile-value policy generic;
- no raw sample Git payloads;
- no credentials/PII from DB1.

## Stop

Do not proceed to comparison if DB2 fails.
