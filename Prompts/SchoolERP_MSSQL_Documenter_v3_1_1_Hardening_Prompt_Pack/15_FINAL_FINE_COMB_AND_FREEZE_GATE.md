# Prompt 15 — Final Fine-Comb Audit and v3.1.1 Freeze Gate

## Objective

Audit the entire repository again after v3.1.1 changes.

Do not accept the implementation report at face value.

## Scope

Audit:

- every production source file;
- every test;
- root launcher/scripts/config;
- Web templates/static assets;
- CI workflow;
- prompt packs;
- packaging/version;
- README/operator/safety/runtime docs;
- v3.1.1 hardening report;
- Git history from `e2188237809efdcc324a79930640628a3975c8d6` to candidate HEAD.

## Named regression search

Explicitly search for recurrence of:

- eager output/Git-export root creation;
- arbitrary SQL;
- unguarded cursor;
- discovered-code execution;
- shell execution;
- raw samples;
- raw unknown profile text in Git export;
- remote/external view sampling;
- misleading report action;
- safe/full mode aliasing;
- Agent execution;
- runtime pytest coupling;
- two-run-only assumptions;
- path-containment regressions;
- external dependency queries;
- missing CI;
- red CI;
- duplicate decorators;
- stale prompt authority.

## Version identity

If release version is bumped to `0.3.1.1` or `0.3.2`, use one intentional value consistently.

Preferred user-facing release name remains:

`v3.1.1`

Package version may follow PEP 440, e.g. `0.3.1.1`, if desired.

Do not casually change versioning scheme without documentation.

## Freeze acceptance

All must be true:

- P0 = 0
- P1 = 0
- unresolved P2 = 0, unless explicitly accepted in writing by product owner
- offline suite green
- GitHub Actions green
- DB1 validation PASS
- DB2 validation PASS if authorized/configured
- Git safety PASS
- external-view rule PASS
- comparison smoke PASS
- documentation truthful
- current prompt authority documented
- no secret/PII in repository diff

Only then change documentation to:

> **MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE**

## Final output

Produce:

- candidate commit SHA;
- full changed-file list;
- acceptance matrix;
- test counts;
- CI run ID;
- live run IDs without PII;
- residual limitations;
- final freeze verdict.

Do not create a tag/release/deployment unless the user explicitly authorizes it.
