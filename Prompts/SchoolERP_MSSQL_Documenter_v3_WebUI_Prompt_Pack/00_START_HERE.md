# SchoolERP Generic MSSQL Database Documenter — v3 Web UI Prompt Pack

This pack supersedes the earlier v2 prompt pack for the MSSQL documentation mini-project.

## Why v3 exists

The earlier design had several important gaps:

1. It required an internal package/CLI but did not require a simple top-level `main.py`.
2. It described `output/` and `git_export/` as project structure, encouraging coding agents to create them before any discovery run.
3. It explicitly said "CLI only", so no browser UI existed.
4. It did not define a secure local web-control layer for starting discovery.
5. It did not define a file-browser/renderer for generated output.
6. It mentioned comparison but did not require a complete run-to-run comparison workflow.
7. It did not require three-way comparison.
8. It did not require path traversal protection, job locking, safe execution endpoints, or browser-side output formatting.
9. Most phase prompts were too short to act as strong implementation contracts.

## v3 target

Build a generic, reusable, read-only MSSQL documentation system with:

- `main.py` as the primary launcher
- CLI and local Web UI
- local-only Flask server
- database discovery/profiling/lineage/documentation
- lazy creation of output folders
- HTML browsing of `output` and `git_export`
- execution of predefined safe discovery modes through the HTML UI
- styled display of Markdown/CSV/JSON/text/SQL/diagrams
- raw-file access without data loss
- search/sort/filter/pagination
- selection of 2 or 3 runs
- side-by-side and delta comparison
- same-database run comparisons
- cross-database comparisons
- Git-safe export
- strict read-only database safeguards

## First prompt to run

Give `01_MASTER_REBUILD_OR_REPAIR_PROMPT.md` to the coding agent.

If an earlier generated project already exists, the coding agent should audit it first and repair it in place where safe.

Do not create fake output runs during implementation.
