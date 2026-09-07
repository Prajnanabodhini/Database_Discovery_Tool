# Prompt 10 — Re-audit Read-Only, Security and Evidence Boundaries

## Objective

After implementation changes, perform a focused security regression audit before the full offline gate.

## Database execution checks

Confirm all execution paths still pass through the read-only cursor and validator.

Search for any new:
- direct raw cursor `.execute()`;
- `executemany`;
- DML/DDL/admin SQL;
- stored-procedure invocation;
- SQL Agent execution;
- external query primitive;
- discovered-code execution.

## Web checks

Confirm:
- loopback restriction;
- CSRF;
- same-origin;
- no arbitrary SQL;
- no arbitrary shell;
- no arbitrary path input escaping configured roots;
- no user-selected subprocess command;
- one heavy job at a time.

## Evidence checks

Confirm:
- secrets sanitized;
- server/login identity sanitized;
- raw sample Git export impossible;
- unknown text profile values handled by new staged policy;
- manifests/checksums updated after transformations;
- source runs not mutated by Git export/report regeneration.

## Runtime laziness

Run import/help/Web app construction/self-test smoke with clean working directory and confirm:
- no `output/`;
- no `git_export/`.

## Deliverable

Add a `Security and Read-Only Re-audit` section to the hardening report.

Any newly discovered P0/P1 stops the sequence.
