# Prompt 01 — Master v3.1.1 Hardening Contract

You are hardening repository `Prajnanabodhini/Database_Discovery_Tool` from authoritative commit:

`e2188237809efdcc324a79930640628a3975c8d6`

The goal is to produce a minimal, auditable v3.1.1 release candidate without disturbing the proven v3.1 architecture.

## Read before editing

Read completely:

- `README.md`
- `SAFETY_MODEL.md`
- `OPERATOR_RUN_GUIDE.md`
- `RUNTIME_OUTPUT_CONTRACT.md`
- `V3_1_FINAL_FILE_AUDIT.md`
- `V3_1_REMEDIATION_REPORT.md`
- `.github/workflows/test.yml`
- `pyproject.toml`
- `main.py`
- all production modules under `src/mssql_database_documenter/`
- all tests under `tests/`
- this v3.1.1 prompt pack

## Required interpretation

Treat existing v3.1 behavior as protected unless a prompt below explicitly changes it.

Do **not** trust current "READY TO FREEZE" prose as an acceptance gate. Acceptance is determined by this pack.

## Primary invariants to preserve

### Database execution

- `ApplicationIntent=ReadOnly`
- autocommit disabled
- rollback/close lifecycle
- fail-closed SQL validator
- final execution-boundary validation
- one SELECT/CTE statement only
- no discovered-code execution
- no stored-program execution
- no Agent execution
- no external query primitives in tool-generated SQL

### Runtime filesystem

- import/help/self-test/Web startup do not create `output/` or `git_export/`
- a real discovery creates evidence lazily
- explicit Git export only
- report regeneration is offline
- comparison stays in memory unless explicit export
- path containment and reparse-point protections remain enabled

### Web

- loopback-only
- CSRF
- same-origin validation
- no arbitrary commands
- predefined jobs only
- redacted logs

### Evidence privacy

- configured credentials and server identity sanitized
- sample payloads excluded from Git by default
- raw Git sample policy prohibited
- masked-only Git sampling preserves source evidence
- final safety audit remains fail-closed

## Work product

Create/update a root file:

`V3_1_1_HARDENING_REPORT.md`

Start it with:

- repository
- starting SHA
- date/time
- working branch
- Python version
- clean/dirty initial working tree
- current CI status
- ordered prompt execution table
- current freeze decision: `NOT READY TO FREEZE`

## Stop rule

Do not make implementation changes in this prompt.

Only baseline, inventory, verify and create the hardening report scaffold.
