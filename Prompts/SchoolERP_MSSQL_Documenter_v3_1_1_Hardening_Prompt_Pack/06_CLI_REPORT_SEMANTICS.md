# Prompt 06 — Correct CLI Report Semantics

## Problem

The Web UI correctly uses offline selected-run:

`regenerate-reports`

But the legacy CLI `report` command currently routes to a fresh `run_all()` discovery.

That is misleading.

## Objective

Make console semantics unambiguous.

## Preferred solution

### Discovery

Keep:

`all`

Meaning:

> Perform a new live read-only discovery and generate its normal reports.

Optionally add clearer alias:

`discover-and-report`

### Offline report regeneration

Add an explicit console action equivalent to Web behavior, for example:

`regenerate-reports --run <manifested-run-path-or-ref>`

Requirements:

- no MSSQL connection;
- requires a real manifested run;
- source run remains byte-for-byte unchanged;
- creates a versioned contained regeneration directory;
- prints sanitized result JSON;
- uses existing `report_regeneration.py`.

### Legacy `report`

Preferred:
- remove it from help; or
- retain only as deprecated alias to `discover-and-report` with an unmistakable warning.

Do not let an operator reasonably interpret `report` as offline regeneration while it connects to MSSQL.

## Tests

- CLI help truthfully explains discovery vs offline regeneration;
- offline regeneration patches `connect` to fail if called;
- source hashes unchanged;
- destination contained;
- existing `all` discovery dispatch remains unchanged;
- Web regeneration unchanged;
- no output root created by CLI help.

## Documentation

Update README and operator guide examples.
