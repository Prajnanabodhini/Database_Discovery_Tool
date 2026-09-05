# Operator Run Guide

## First-time setup

From the project directory in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
```

For first validation, set `MSSQL_DATABASE` to one explicitly approved database and
leave `MSSQL_DATABASES` empty. Configure either Windows trusted authentication or
both SQL-authentication fields—never both authentication methods.

Launch the dashboard:

```powershell
.\.venv\Scripts\python.exe main.py
```

The browser opens `http://127.0.0.1:8765/` by default. The application rejects a
non-loopback `WEB_HOST`; do not expose it to a network interface without a separate
security review.

## Recommended validation sequence

Complete and review each step before advancing:

1. **Dry Run** — validates every registered project query without connecting or creating output.
2. **Test Connection** — verifies the configured server/database with guarded identity queries; it creates no run.
3. **Metadata** — creates the first real manifested run.
4. Review the run under **Output evidence**, including warnings, errors, manifest, and checksums.
5. **Metadata + Logic** — adds static programmable-object, dependency, lineage, and pipeline analysis.
6. Review uncertainty/evidence classifications and any access limitations.
7. **Safe Profile** — adds threshold-controlled profiling and masked samples.
8. Review resource impact, skipped-large/unknown-size statuses, masking, and quality findings.
9. Open `99_Git_Handoff/MASKING_SAFETY_AUDIT.json` and confirm it reports `PASS`.
10. **Create Git export** — explicitly copy only the reviewed run. The exporter repeats
    secret, profile-value, low-cardinality, sample-masking, containment, file-type, and
    transient-file checks before copying anything.

Use **Full Read-Only** only in an approved maintenance window after the earlier modes
have been validated. “Read-only” prevents mutation but does not eliminate CPU, I/O,
locking, or network impact.

## Multiple databases and comparison

Only after the one-database sequence succeeds, clear `MSSQL_DATABASE` and set the
comma-separated `MSSQL_DATABASES` allowlist. Discovery processes configured databases
strictly one at a time and stops if the current database fails.

On **Compare runs**, select Run A and Run B, plus optional Run C. Review mixed-mode,
cross-database, missing-evidence, and partial-run warnings. Browser comparison remains
in memory; HTML/CSV/JSON files are written only by **Compare and export**.

## Stop and recovery

- **Cancel safely** requests cancellation at the next stage boundary; it does not kill an in-flight ODBC call.
- Failed or cancelled real attempts retain a truthful partial manifest for diagnosis.
- Never delete or overwrite prior run directories to retry; start a new uniquely named run.
- Keep `.env`, `output/`, and `git_export/` out of source control unless a reviewed sanitized export is deliberately handed off.

## Historical-run warning

Runs produced before the 2026-08-31 profile-masking repair may contain raw minimum or
maximum profile values for columns later classified as sensitive. Do not export or
share those historical runs. Create a fresh run with the repaired version and review
its masking safety audit. A generated checklist is evidence of executed checks, not a
substitute for operator review and organizational approval.
