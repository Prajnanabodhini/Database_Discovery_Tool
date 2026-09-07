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
| `SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack` | ACTIVE UNTIL COMPLETED | Yes, sequentially and only when the next numbered prompt is explicitly authorized |

Historical prompts and execution records are evidence, not current
instructions. Keep them for provenance and auditability; do not delete them.
They must not be used to revert the current implementation to an earlier
prompt generation's architecture or behavior.

The v3.1.1 hardening pack is the only active prompt authority. Its numbered
prompts must be executed in order, with every required gate completed and
reported before the next prompt starts. Its live-database prompts remain
subject to their explicit authorization gates.

After the v3.1.1 final fine-comb and freeze gate completes, change the hardening
pack's status in this table to `EXECUTED / HISTORICAL` and its execution status
to `No`.
