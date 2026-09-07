# Prompt 07 — Metadata Inventory Connection-Failure Lifecycle

## Problem

The staged metadata-only `run_inventory()` creates a run directory before the initial DB connection.

If the initial connection fails before normal evidence initialization, an unmanifested run directory can remain.

Every runtime evidence directory should be either:

- a truthful manifested run, including FAILED/PARTIAL; or
- absent if no run was actually established.

## Objective

Make metadata inventory lifecycle truthful and deterministic.

## Acceptable solution A — preferred

Once a run root is reserved, initialize minimum control evidence immediately:

- run ID
- database
- sanitized configuration
- stage status
- `run_summary.json`
- `manifest.json`

If connection fails:
- status = `FAILED`
- no false "metadata completed" claim
- sanitized error recorded
- checksums generated
- no secrets

## Acceptable solution B

If the initial connection fails before any evidence work:
- remove the newly created empty run directory safely;
- never remove a pre-existing path;
- never escape the configured output root.

## Required invariant

No unmanifested orphan run directory may remain after a normal handled connection failure.

## Tests

- simulated initial connection failure;
- no secret in exception/evidence;
- outcome is manifested FAILED or absent;
- pre-existing directories untouched;
- path containment preserved;
- normal successful inventory unchanged;
- metadata query-level failures still produce header-only artifacts and warnings as designed.
