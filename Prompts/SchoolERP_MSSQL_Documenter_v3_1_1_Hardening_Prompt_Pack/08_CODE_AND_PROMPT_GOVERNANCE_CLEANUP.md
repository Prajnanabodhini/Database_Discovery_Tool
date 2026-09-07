# Prompt 08 — Code Cleanup and Prompt Authority Governance

## Scope

Only two cleanup areas are authorized.

### A. Duplicate decorator

Remove the duplicate consecutive:

```python
@staticmethod
@staticmethod
```

from the lineage stage helper.

Do not refactor unrelated lineage logic.

### B. Prompt authority index

Create:

`Prompts/README.md`

It must explicitly classify every top-level prompt generation.

Minimum authority table:

| Prompt set | Status | Can be executed now? |
|---|---|---|
| `MSSQL_DB_Documentation_Prompt` | HISTORICAL | No |
| `SchoolERP_MSSQL_Documenter_v3_WebUI_Prompt_Pack` | HISTORICAL / SUPERSEDED | No |
| `V3_PROMPT_PACK_SEQUENTIAL_EXECUTION_2026-09-05.md` | HISTORICAL EXECUTION RECORD | No |
| `SchoolERP_MSSQL_Documenter_v3_1_Remediation_Prompt_Pack` | EXECUTED / HISTORICAL IMPLEMENTATION SPEC | No |
| v3.1.1 hardening pack | ACTIVE UNTIL COMPLETED | Yes, sequentially |

Also state:

- historical prompts are evidence, not current instructions;
- do not delete them;
- current implementation is not to be reverted to an earlier prompt's architecture;
- after v3.1.1 freeze, mark this hardening pack EXECUTED/HISTORICAL.

## Tests

Compile/import after decorator cleanup.

No functional behavior should change.
