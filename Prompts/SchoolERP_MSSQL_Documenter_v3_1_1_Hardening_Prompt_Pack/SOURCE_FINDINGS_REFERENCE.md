# Source Findings Reference for v3.1.1

This document summarizes the independent audit findings that created this hardening pack.

## Authority

Audited repository HEAD:

`e2188237809efdcc324a79930640628a3975c8d6`

Implementation base:

`54477bbea476c4786c7285a9c8fd8075d04f13be`

## P1-1 — CI red

GitHub Actions on both v3.1 commits failed the Windows/Python 3.11 offline suite.

Observed final test result:

- 159 passed
- 2 failed
- 241 subtests passed

Root cause:
Windows short vs long temp path representation.

The failures were in:
- runtime self-test cwd assertion;
- Web report-regeneration containment assertion.

The final runtime-root no-evidence check still passed.

## P1-2 — External view sampling

`profiling/sampler.py` allows bounded view sampling but receives no dependency-safety input.

The lineage subsystem separately understands:
- target server;
- target database;
- external SQL constructs;
- external synonyms;
- opaque dependencies.

The two domains are not currently joined before a view SELECT is executed.

## P1-3 — Generic Git profile privacy

Git sample payloads are strong:
- default exclude;
- masked-only available;
- raw forbidden.

But other committed profile artifacts carry min/max/low-cardinality values.

Sensitivity fallback for arbitrary unknown text is `Unknown/PRESERVE`.

Therefore future generic databases can contain semantically sensitive strings that do not match existing name/value heuristics.

## P2-1 — CLI report

`mssql_database_documenter.cli` sends both `all` and `report` to `run_all()`.

Web report regeneration is offline, so CLI terminology is inconsistent.

## P2-2 — Inventory lifecycle

Metadata-only inventory reserves a run root before initial connection.

Connection failure can occur before normal manifest finalization.

## P3-1 — Duplicate decorator

`lineage/stages.py` contains two consecutive `@staticmethod` decorators for `_programmable_headers`.

## P3-2 — Prompt governance

Multiple historical prompt generations coexist under `Prompts/` without one authority/supersession index.

## Important positive findings to preserve

- fail-closed SQL validator;
- read-only connection;
- no discovered-code execution;
- modular full-run design;
- view/large table sampling;
- sensitivity reconciliation;
- SQL Agent static analysis;
- expanded metadata;
- offline self-test;
- offline report regeneration;
- 2/3-run comparison;
- static comparison HTML;
- Git sample exclusion;
- path controls;
- local Web security.
