# Prompt 04 — Prevent Indirect External-System Access During View Sampling

## Problem

The v3.1 sampler correctly supports views using a bounded outer SELECT, but a local view can internally reference:

- linked servers;
- another database;
- `OPENQUERY`;
- `OPENROWSET`;
- `OPENDATASOURCE`;
- external synonyms;
- provider/external access;
- dynamic or otherwise opaque dependencies.

A tool-generated query such as:

```sql
SELECT TOP (100) * FROM [dbo].[SomeView]
```

can cause SQL Server to access a remote system even though the Python SQL validator sees only a local SELECT.

That violates the product boundary:

> External dependencies may be discovered and documented, but must not be queried automatically.

## Objective

Introduce a **fail-closed view-sampling eligibility gate**.

## Required design

Create a domain-level decision such as:

`ViewSampleEligibility`

or equivalent.

The sampler/orchestrator must decide whether a view is safe to sample based only on already-discovered metadata/static evidence.

### Deny sampling if any of these are true

- dependency has a non-empty `target_server`;
- dependency targets another database outside the current configured database;
- definition/static evidence contains `OPENQUERY`, `OPENROWSET`, or `OPENDATASOURCE`;
- dependency goes through an external/remote synonym;
- the view is marked dynamic/opaque in a way that prevents proving local-only data access;
- external dependency evidence is incomplete but indicates possible out-of-database execution;
- dependency resolution is explicitly inaccessible/opaque and safety cannot be proven.

### Required status

Record a truthful non-error status such as:

`SKIPPED_EXTERNAL_OR_OPAQUE_VIEW_DEPENDENCY`

The status must appear in sample/index/coverage evidence.

### Important

Do not silently reinterpret "no dependency rows" as proof of safety when:
- the view definition is unavailable/encrypted;
- dependency discovery failed;
- static analysis is opaque.

Fail closed.

## Interaction with modes

This restriction applies to:
- `safe-profile`
- `full-readonly`

`full-readonly` is still read-only; it is not authorization to traverse remote systems.

Do **not** add an enable flag for remote sampling in v3.1.1 unless the product owner explicitly requests it later.

## Tests

Add tests for:

1. local-only view → sample allowed;
2. three-part reference to current database → allowed if unambiguously local;
3. other database reference → skipped;
4. four-part linked-server reference → skipped;
5. OPENQUERY → skipped;
6. OPENROWSET → skipped;
7. OPENDATASOURCE → skipped;
8. external synonym → skipped;
9. encrypted/unavailable/opaque definition with unresolved dependency risk → skipped;
10. safe table sampling remains unaffected;
11. no remote database connection helper is introduced;
12. generated SQL still passes the existing read-only validator.

## Evidence

Update the hardening report with:
- new decision contract;
- evidence sources used;
- exact skip statuses;
- tests;
- confirmation that external systems are never intentionally queried.
