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

## Current v3.1.1 validation status

Fresh Prompts 12–14 validation completed on 2026-09-07 for both configured
databases. Dry-run, connection, metadata, metadata+logic, safe-profile,
independent masking audit, explicit exclude-samples Git export, offline report
regeneration, and real two/three-run comparison gates passed. Each
safe-profile run records one contained object-level warning for an inaccessible
view; the object was skipped while all stages continued truthfully.

The old failed output `20260906_150848` remains unsafe local diagnostic evidence;
never edit, share, or export it. Full-readonly was not separately authorized during
the remediation validation and was not rerun.

A post-freeze audit found and repaired an initial discovery run-root junction
escape. The candidate rejects database-parent reparse points before inventory
or full discovery can create evidence outside `OUTPUT_ROOT`. Its local gates
and Windows/Python 3.11 GitHub Actions run `34141997707` pass:
**MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE.** No tag, release,
deployment, database change, or production maintenance window has been
created.

## Offline developer self-test

Developer verification is separate from database discovery:

```powershell
.\.venv\Scripts\python.exe main.py self-test
```

The environment-independent command `python main.py self-test` is the local equivalent
of the GitHub offline developer quality gate.

This explicit command uses fixed arguments to run the offline test suite. It does not
load `.env`, connect to MSSQL, create an `output/` run, or create `git_export/` evidence.
Its summary is sanitized, tests marked `live` are excluded, and pytest cache creation is
disabled. If pytest or the `tests/` tree is not installed, the command fails as a
developer diagnostic; normal discovery remains available because runtime stage 21 never
invokes pytest or reads test source. No Web self-test action is exposed.

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

## What each mode actually permits

| Mode | Catalog/logic | Data reads | Effective depth |
|---|---|---|---|
| Metadata | Structural catalog only | None | Lowest-impact real run |
| Metadata + Logic | Catalog, stored text, static dependencies, pipeline metadata | None | No discovered procedure, trigger, function, job, or definition is executed |
| Safe Profile | Metadata + logic | Bounded samples, profiles, and relationship checks | Conservative configured thresholds; exact counts remain disabled |
| Full Read-Only | Everything in Safe Profile | Larger bounded limits and optional exact counts | Separate configuration, extended validation, and mandatory hard ceilings |

The label is not the only evidence. Open `00_Run_Metadata/RUN_CONFIGURATION.json`,
`run_summary.json`, or `manifest.json` and inspect `resolved_mode_policy` to see the
effective branches and limits used for that run.

The metadata stage also writes `02_Server_Database/MSSQL_FEATURE_SUPPORT_OVERVIEW.csv`
and `.md`. Review every row: `ABSENT` means the corresponding catalogue query
succeeded with zero matching rows visible to the reader (metadata visibility can
still limit scope); `INACCESSIBLE` means permissions prevented a
conclusion; `UNSUPPORTED` means the SQL Server version or edition lacks the catalog
surface. These states must not be treated as interchangeable.

Optional database-principal metadata is disabled by default. Enable it only through
`DISCOVER_SECURITY_METADATA=true` after approval. The output contains hashed identity
fingerprints and structural attributes, not raw principal names or grants. Keep it
disabled when the additional security inventory is unnecessary.

Full Read-Only configuration uses `FULL_READONLY_SAMPLE_ROW_LIMIT`,
`FULL_READONLY_PROFILE_THRESHOLD`, `FULL_READONLY_EXACT_COUNT_THRESHOLD`,
`FULL_READONLY_RELATIONSHIP_THRESHOLD`, `FULL_READONLY_LOW_CARDINALITY_LIMIT`, and
`FULL_READONLY_EXTENDED_VALIDATION`. Exact counts also require
`PROFILE_EXACT_ROW_COUNTS=true`; they are never enabled in the other three modes.

Non-overridable ceilings are 500 safe sample rows, 2,000 Full Read-Only sample rows,
1,000,000 safe-profile rows, 10,000,000 Full Read-Only profile/relationship rows,
1,000,000 rows for an exact count, 100 safe low-cardinality values, and 1,000 Full
Read-Only low-cardinality values. A policy exceeding a ceiling is rejected before a
run directory is created.

## Multiple databases and comparison

Only after the one-database sequence succeeds, clear `MSSQL_DATABASE` and set the
comma-separated `MSSQL_DATABASES` allowlist. Discovery processes configured databases
strictly one at a time and stops if the current database fails.

On **Compare runs**, select Run A and Run B, plus optional Run C. Review mixed-mode,
cross-database, missing-evidence, and partial-run warnings. Browser comparison remains
in memory; HTML/CSV/JSON files are written only by **Compare and export**. Added,
Changed, and Removed filters inspect all interval statuses and timeline events, not just
one headline status. An item can therefore appear in multiple applicable filters; this
is expected for added-then-changed, reverted, and remove/re-add histories.

Global comparison totals count all rows across all displayed/exported categories.
Selected-category totals count all rows matching the current filters, not only the
current page. Primary-status counts always sum to the stated row count. Interval and
timeline-event counts are occurrences and may be higher because one row can carry
multiple events. JSON and CSV are canonical machine outputs; static HTML is the complete
human-readable presentation and requires no JavaScript when opened in the safe browser.

## Offline report regeneration

Use **Regenerate Reports** only after an output run already exists:

1. On the dashboard, select one manifested canonical run in the Offline presentation
   refresh panel.
2. Select **Regenerate Reports** and wait for the controlled job to complete.
3. Open the returned versioned folder below `output/report_regenerations/`.
4. Review its Markdown/HTML report, regeneration manifest, and checksums.

This action does not load connection settings into a database session, open MSSQL,
execute SQL, refresh catalogues, or modify the selected run. It hashes every source
file before and after generation and creates a new destination for every request.
If the stored evidence is stale or incomplete, perform a new approved discovery
instead. A regenerated report is a presentation copy, not a sanitized Git export;
the separate Git-export safety review still applies to canonical runs.

The equivalent console action is:

```powershell
.\.venv\Scripts\python.exe main.py regenerate-reports --run "output:School/run_20260907_120000"
```

You may also supply the contained path of the manifested run. This command is
offline and presentation-only. By contrast, these commands connect to MSSQL and
create a new discovery run with its normal reports:

```powershell
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env --mode safe-profile all
.\.venv\Scripts\python.exe -m mssql_database_documenter --env-file .env --mode safe-profile discover-and-report
```

The former `report` command is no longer accepted because its name did not reveal
that it started a live database discovery.

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
