# Prompt 15 — Final Fine-Comb Audit and v3.1 Freeze

Audit every project-owned source/config/test/doc file: purpose, callers, reads, local writes, DB access, Web exposure, safety, tests, status.

Search for regressions: eager mkdir, startup output/export, arbitrary SQL, unguarded cursor, discovered-code execution, shell/unsafe subprocess, secrets/raw samples, misleading reports action, script-dependent comparison HTML, safe/full mode aliasing, Agent execution, monolithic leftovers, runtime pytest, missing metadata contracts, 2-run-only assumptions, 3-run filter gaps, missing CI.

Required docs: `V3_1_REMEDIATION_REPORT.md`, `V3_1_FINAL_FILE_AUDIT.md`, updated README/operator/safety/help and acceptance checklist.

Declare `MSSQL DOCUMENTATION TOOL v3.1 — READY TO FREEZE` only if all P0/P1 resolved, P2 resolved/explicitly accepted, offline gates pass, and live gates pass if authorized. If live access was not authorized, declare `CODE/OFFLINE READY — LIVE VALIDATION PENDING`.
