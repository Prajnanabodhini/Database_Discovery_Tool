# SchoolERP MSSQL Documenter v3.1 — Remediation Prompt Pack

Repository: `Prajnanabodhini/Database_Discovery_Tool`  
Target branch: `main`  
Audited/frozen source SHA: `1c608d12d7c0f107931144dbbdc4e536865ab546`  
Pack date: 2026-09-06

## Purpose

Repair the current MSSQL Database Discovery Tool **in place**. Do not rebuild it.

Preserve the working v3 foundations: root `main.py`, Windows launchers, generic `.env`, multi-database sequential processing, strict read-only SQL/ODBC safety, lazy `output/`, explicit `git_export/`, localhost Flask UI, CSRF/same-origin controls, controlled jobs, dual-root file browser, renderers, manifests, 2/3-run comparison, evidence audit, Git export, per-object docs and diagrams.

## Before changing anything

1. Read `01_MASTER_REMEDIATION_PROMPT.md` completely.
2. Read `ACCEPTANCE_MATRIX.md` and `SOURCE_AUDIT_REFERENCE.md`.
3. Confirm repository HEAD and working tree.
4. If `main` is no longer `1c608d12d7c0f107931144dbbdc4e536865ab546`, compare the new HEAD to this SHA and adapt the repair; preserve newer correct work.
5. Never delete/rewrite historical `output/` or `git_export/`.
6. Never commit `.env`, credentials, runtime evidence, real samples, caches or logs.
7. Do not run live DB discovery until the offline gate passes and the operator explicitly authorizes it.

## Preferred execution order

Run the numbered prompts sequentially and STOP after each prompt:

1. `02_BASELINE_AND_GUARDRAILS.md`
2. `03_PII_AND_GIT_EXPORT_HARDENING.md`
3. `04_SAMPLE_COVERAGE_VIEWS_LARGE_TABLES.md`
4. `05_DISCOVERY_MODE_SEMANTICS.md`
5. `06_SQL_AGENT_PIPELINE_LINEAGE.md`
6. `07_MSSQL_METADATA_COMPLETENESS.md`
7. `08_MODULARIZE_FULLRUN.md`
8. `09_RUNTIME_SELF_TEST_DECOUPLING.md`
9. `10_COMPARISON_AND_EXPORT_FIXES.md`
10. `11_REPORT_REGENERATION_ACTION.md`
11. `12_CI_AND_DEVELOPER_QUALITY_GATE.md`
12. `13_OFFLINE_REGRESSION_AND_SECURITY_GATE.md`
13. `14_LIVE_READONLY_VALIDATION.md` — only with explicit approval
14. `15_FINAL_FINE_COMB_AND_FREEZE.md`

For one-shot Codex execution, use `01_MASTER_REMEDIATION_PROMPT.md`; it must still obey every internal gate.

## Completion rule

Do not freeze v3.1 until all P0/P1 findings are resolved, the offline suite passes, privacy is fail-safe, view/large-table samples work safely, mode semantics differ, Agent lineage is improved without execution, metadata coverage is expanded, `fullrun.py` is modularized, pytest is removed from live discovery, comparison/export issues are fixed, CI exists, and a final fine-comb audit is produced.
