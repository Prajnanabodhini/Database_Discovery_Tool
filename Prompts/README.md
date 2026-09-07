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
| `SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack` | EXECUTED / HISTORICAL | No |

Historical prompts and execution records are evidence, not current
instructions. Keep them for provenance and auditability; do not delete them.
They must not be used to revert the current implementation to an earlier
prompt generation's architecture or behavior.

The v3.1.1 hardening pack completed its original sequence and the authorized
Prompt 07, 09, 10, and 15 corrective cycle on 2026-09-07. The repaired
candidate passed its local gates and Windows/Python 3.11 CI. The pack is
retained as historical specification and execution provenance, not as a
currently executable prompt source. Current release evidence is recorded in
`V3_1_1_HARDENING_REPORT.md`.
