# SchoolERP MSSQL Documenter v3.1.1 Hardening Prompt Pack

**Repository:** `Prajnanabodhini/Database_Discovery_Tool`  
**Authoritative starting branch:** `main`  
**Authoritative starting HEAD:** `e2188237809efdcc324a79930640628a3975c8d6`  
**v3.1 implementation commit:** `54477bbea476c4786c7285a9c8fd8075d04f13be`  
**Original v3 baseline:** `1c608d12d7c0f107931144dbbdc4e536865ab546`  
**Pack date:** 2026-09-07

## Purpose

This pack performs a **targeted v3.1.1 hardening pass** on the existing MSSQL Database Discovery Tool.

It is **not** a rewrite, architecture reset, feature expansion, database migration, or new product version.

The existing v3.1 implementation is substantially correct and must be preserved. The work in this pack exists to close the remaining release/freeze gaps found by the independent end-to-end audit.

## Current independent decision

> **v3.1 is NOT READY TO FREEZE.**

The repository documentation at `e2188237809efdcc324a79930640628a3975c8d6` currently says that v3.1 is ready to freeze. That declaration is superseded for implementation purposes by this hardening pack until all v3.1.1 gates pass.

## Mandatory P1 fixes

1. Fix the two Windows CI path-canonicalization failures and obtain a green GitHub Actions run.
2. Prevent automatic table/view sampling from indirectly querying external systems through externally backed or opaque views.
3. Harden Git-export handling of data-bearing profile values so unknown text cannot silently be committed as raw values.

## Mandatory P2 fixes

4. Correct the misleading CLI `report` semantics.
5. Make metadata-only inventory connection failure produce either truthful failed evidence or no run root.

## Mandatory P3 cleanup

6. Remove the duplicate `@staticmethod` decorator in lineage stages.
7. Add an explicit prompt authority/supersession index.

## Non-negotiable safety

- MSSQL discovery remains **strictly read-only**.
- Never execute stored procedures, SQL Agent jobs, PowerShell, CmdExec, SSIS, arbitrary SQL, or discovered code.
- Never run INSERT/UPDATE/DELETE/MERGE/DDL/admin SQL.
- Never add a Web endpoint that accepts arbitrary SQL/shell/file-system commands.
- Never expose the local Web UI beyond loopback.
- Never add raw sample payloads to Git export.
- Never weaken the current SQL validator, path containment, Web CSRF/same-origin controls, masking, secret redaction, output-root laziness, or sequential multi-database behavior.
- Do not mutate live databases for testing.
- Do not add MariaDB support in this pack.
- Do not refactor unrelated code for style.
- Do not delete historical validation documents.
- Do not rewrite Git history.

## Execution model

Run the prompts **strictly in numeric order**.

After each numbered prompt:

1. complete only that prompt's scope;
2. run its specified tests;
3. inspect the diff;
4. update `V3_1_1_HARDENING_REPORT.md`;
5. stop and report:
   - files changed,
   - behavior changed,
   - tests run/results,
   - unresolved findings,
   - whether the next prompt is safe to start.

Do not skip a failed gate.

## Live validation authorization

Prompts 12–14 are live-read-only validation prompts.

Do not execute them until:

- all offline gates pass;
- CI is green;
- the user/operator has confirmed the configured MSSQL environments are authorized for read-only validation.

All live work remains SELECT/metadata-only through the existing safety boundary.
