# Prompt 06 — SQL Agent and Pipeline Lineage

## Objective
Improve scheduled pipeline documentation while preserving inspect-never-execute.

1. Make Agent step command text available only to sanitizer/static parser.
2. Never execute it.
3. Persist command SHA plus safe derived references; sanitized command text only if provably safe.
4. TSQL: extract conservative READ/WRITE/CALL/database/external refs; dynamic SQL stays opaque/inference.
5. SSIS/PowerShell/CmdExec/etc: record sanitized invocation hints and opaque/external classification only.
6. Add `SQL_AGENT_STEP_REFERENCES.csv` and `SQL_AGENT_PIPELINE_EDGES.csv`.
7. Merge safe edges into pipeline/lineage with evidence classes.

Tests: EXEC, INSERT...SELECT, three-part name, dynamic SQL, fake-secret PowerShell, CmdExec, SSIS-like fixture. Fake secret must never persist.

STOP.
