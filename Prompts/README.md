# Prompt Authority and Supersession Index

This file is the authority index for every prompt generation stored directly
under `Prompts/`. It determines whether a prompt set is an active instruction
source or retained historical evidence.

| Prompt set | Status | Can be executed now? |
|---|---|---|
| `MSSQL_DB_Documentation_Prompt` | HISTORICAL | No |
| `REPAIR_AND_LAYMAN_UI_IMPLEMENTATION_PLAN.md` | EXECUTED / HISTORICAL IMPLEMENTATION PLAN | No |
| `SchoolERP_MSSQL_Documenter_v3_WebUI_Prompt_Pack` | HISTORICAL / SUPERSEDED | No |
| `V3_PROMPT_PACK_SEQUENTIAL_EXECUTION_2026-09-05.md` | HISTORICAL EXECUTION RECORD | No |
| `SchoolERP_MSSQL_Documenter_v3_1_Remediation_Prompt_Pack` | EXECUTED / HISTORICAL IMPLEMENTATION SPEC | No |
| `SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack` | ACTIVE — REOPENED TARGETED REMEDIATION | Yes, only Prompts 07, 09, 10, and 15 in the authorized sequence |

Historical prompts and execution records are evidence, not current
instructions. Keep them for provenance and auditability; do not delete them.
They must not be used to revert the current implementation to an earlier
prompt generation's architecture or behavior.

The v3.1.1 hardening pack originally completed through its final gate on
2026-09-07. A later audit reopened Prompts 07, 09, 10, and 15 to repair an
initial run-root junction containment gap. Prompts 07, 09, and 10 have passed
locally; Prompt 15 remains active until the repaired candidate has green CI.
Current release evidence is recorded in `V3_1_1_HARDENING_REPORT.md`.
