# SchoolERP MSSQL Documenter v3.1.1 Hardening Report

## Header

- Repository: `Prajnanabodhini/Database_Discovery_Tool`
- Starting SHA: `e2188237809efdcc324a79930640628a3975c8d6`
- Working branch: `main`
- Current hardening branch: `v3.1.1-hardening`
- Candidate SHA: not established
- Baseline date/time: `2026-09-07T10:30:21.0332931+05:30`
- System Python: `3.11.9`
- Project `.venv` Python: `3.13.14`
- Package: `mssql-database-documenter 0.3.1`
- Initial working tree: dirty only because the complete v3.1.1 hardening prompt-pack directory is untracked; no tracked application files were modified
- Initial CI: **FAILED** for the starting SHA; GitHub Actions run `34077479576`, completed `2026-09-07T02:48:34Z`
- Initial CI URL: `https://github.com/Prajnanabodhini/Database_Discovery_Tool/actions/runs/34077479576`

## Current freeze decision

> **NOT READY TO FREEZE**

The earlier v3.1 freeze-readiness declaration is superseded by the v3.1.1 hardening pack until every mandatory gate has passed.

## Authority and protected scope

- v3.1 implementation commit: `54477bbea476c4786c7285a9c8fd8075d04f13be`
- Original v3 baseline: `1c608d12d7c0f107931144dbbdc4e536865ab546`
- Active instructions: `Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack`
- Prompts must run strictly in numeric order, stopping with evidence after each prompt.
- Live validation is prohibited until the offline gate passes, GitHub Actions is green, and the operator explicitly authorizes the configured MSSQL environments.

The existing v3.1 architecture is protected. This pass must remain targeted and must not become a rewrite, feature expansion, database migration, external-system traversal, remote Web deployment, or unrelated refactor.

## Required corpus review

Prompt 01's required pre-edit corpus was read completely at the starting SHA:

- nine named root, workflow, packaging, and entrypoint files;
- all 52 production Python files under `src/mssql_database_documenter/`;
- all 13 production Web template/static asset files under that package;
- all 25 test files under `tests/`;
- all 23 files in the v3.1.1 hardening prompt pack.

Total unique files read: `122` (`824,006` bytes; `15,620` lines).

The review confirmed the protected v3.1 safety baseline: read-only connection intent, autocommit disabled, rollback/close lifecycle, fail-closed SQL validation, guarded cursor execution, no discovered-code or stored-program execution, lazy runtime roots, explicit Git export, offline regeneration, in-memory comparison until explicit export, path containment, loopback-only Web access, CSRF/same-origin controls, redacted logs, and sequential multi-database behavior.

## Prompt execution ledger

| Prompt | Status | Files changed | Tests | Notes |
|---|---|---|---|---|
| 00 | COMPLETE | None | Not required | Authority, safety, sequence, and live gates acknowledged. |
| 01 | COMPLETE | `V3_1_1_HARDENING_REPORT.md` | Not required | Baseline/report scaffold only; no implementation change. |
| 02 | COMPLETE | `V3_1_1_HARDENING_REPORT.md` | 159 passed, 2 skipped, 241 subtests | Clean isolated baseline; compile PASS; no DB or runtime roots. |
| 03 | LOCAL PASS — CI PENDING | `tests/test_runtime_self_test.py`, `tests/test_web_app.py`, report | 2 targeted; 10 related; full suite 159 passed | Awaiting approved commit/push and green Windows/Python 3.11 Actions run. |
| 04 | NOT STARTED | None | Not run | External/opaque view sampling gate. |
| 05 | NOT STARTED | None | Not run | Git-export profile-value privacy. |
| 06 | NOT STARTED | None | Not run | CLI report semantics. |
| 07 | NOT STARTED | None | Not run | Inventory connection-failure lifecycle. |
| 08 | NOT STARTED | None | Not run | Decorator and prompt authority cleanup only. |
| 09 | NOT STARTED | None | Not run | Targeted regression suite. |
| 10 | NOT STARTED | None | Not run | Security/read-only/evidence re-audit. |
| 11 | NOT STARTED | None | Not run | Full offline and green-CI gate. |
| 12 | NOT AUTHORIZED | None | Not run | DB1; blocked by offline, CI, and operator gates. |
| 13 | NOT AUTHORIZED | None | Not run | DB2; also requires DB1 PASS. |
| 14 | NOT AUTHORIZED | None | Not run | Export/regeneration/comparison smoke. |
| 15 | NOT STARTED | None | Not run | Final fine-comb and freeze decision. |

## Initial priority register

| Severity | Count | Open items |
|---|---:|---|
| P0 | 0 | None identified by the source findings. |
| P1 | 3 | Green Windows CI; fail-closed external/opaque-view sampling; Git-export privacy for unknown profile values. |
| P2 | 2 | Truthful CLI report semantics; deterministic inventory connection-failure evidence lifecycle. |
| P3 | 2 | Duplicate lineage `@staticmethod`; prompt authority/supersession index. |

## Baseline observations

- Repository identity, branch, and SHA match the pack exactly.
- The latest workflow for the starting SHA is red; live validation is therefore prohibited.
- GitHub CLI is unavailable, so CI status was obtained from the GitHub Actions API.
- The shell's `python` is 3.11.9; the repository `.venv` is 3.13.14. Prompt 02 must record the interpreter selected for its reproducible baseline. CI remains Windows/Python 3.11.
- The untracked hardening pack is the only initial working-tree difference.
- Ignored `output/` and `git_export/` directories are present from earlier work. Prompt 01 did not create or modify them; Prompt 02 must use an explicitly controlled absent-before/after baseline for its lazy-root gate.
- `IMPLEMENTATION_REPORT_TEMPLATE.md` and `ACCEPTANCE_MATRIX.md` reuse `H-01` through `H-05` at different granularities. This report treats the acceptance matrix's `H-01` through `H-35` identifiers as authoritative and otherwise uses descriptive finding names.

## Prompt 01 evidence

- Files changed: created `V3_1_1_HARDENING_REPORT.md` only.
- Behavior changed: none.
- Tests run: none; this prompt permits baseline/inventory work only.
- Database connections: none.
- Runtime output or Git-export roots created or modified by Prompt 01: none; pre-existing ignored roots remain present.
- Unresolved findings: all three P1, two P2, and two P3 items remain open as expected.
- Next prompt: Prompt 02 is safe to start; it must baseline and classify without fixing findings.

## Prompt 02 — Baseline, branch, diff and guardrails

### Repository and branch

- Remote: `https://github.com/Prajnanabodhini/Database_Discovery_Tool.git`
- Repository root: `D:/School ERP projects/Database_Discovery_Tool`
- Approved base branch: `main`
- Base and current HEAD: `e2188237809efdcc324a79930640628a3975c8d6`
- Hardening branch created from that exact SHA: `v3.1.1-hardening`
- No force update or history rewrite was performed.
- Initial tracked-file diff: none.
- Initial untracked content: the hardening prompt pack and, after Prompt 01, this report.

Recorded history: `e218823` (main/origin), `54477bb` (v3.1 implementation), and `1c608d1` (original baseline).

### Package, interpreter and inventory

- Package: `mssql-database-documenter 0.3.1`; required Python `>=3.11`
- System Python: `3.11.9`
- Selected project environment: Python `3.13.14`, pytest `9.1.1`
- Production Python files: `52`
- Test Python files: `25`
- Suite outcomes: 159 passed, 2 skipped, and 241 subtests passed.

The first clean-worktree attempt used system Python 3.11.9. Compile passed, but pytest could not start because that interpreter lacks pytest. This was an environment failure, not a test failure. No dependency was changed. The complete baseline then passed with the existing project environment.

### Reproducible offline baseline

The required commands ran in a temporary detached Git worktree at the authoritative SHA, preserving earlier ignored evidence while providing a controlled clean root.

| Check | Result |
|---|---|
| Isolated HEAD | `e2188237809efdcc324a79930640628a3975c8d6` |
| `output/` before and after | absent / absent |
| `git_export/` before and after | absent / absent |
| compileall command | PASS, exit 0 |
| non-live pytest command | PASS, exit 0 |
| pytest result | 159 passed, 2 skipped, 241 subtests passed in 8.50s |
| MSSQL connection | not attempted |

The verified temporary worktree was removed afterward. Pre-existing ignored runtime directories in the operator's main workspace were not touched.

### Required source-search classification

- `execute(`: database calls use `ReadOnlyCursor`; its proxy revalidates SQL immediately before the underlying driver call. Inventory, full-run, CLI, and Web connection checks construct the proxy first.
- `executemany`: present only as a denied proxy method that raises `UnsafeSqlError`.
- `exec(`, `eval(`, `os.system`, and `shell=True`: no executable production use.
- `subprocess`: only the fixed offline self-test pytest argv, with no shell, a fixed repository cwd, timeout, and captured output.
- `OPENQUERY`, `OPENROWSET`, and `OPENDATASOURCE`: fail-closed validator patterns and static lineage classification only; no generated query invokes them. The indirect-view risk remains open for Prompt 04.
- `xp_cmdshell`: no production occurrence.
- `sp_executesql` and `EXEC`: static lineage detection and SQL blocking only; no invocation path.
- DML, DDL, and admin terms: validator deny lists, lineage text classification, or language false positives such as dictionary `update`, HTTP `DELETE`, and a `create` parameter. No executable write/admin SQL was found.
- `mkdir`: operation-scoped evidence writers and contained destination helpers. No import-time eager root creation was found. Inventory reserves its run root before connection; the known failure-lifecycle risk remains assigned to Prompt 07.
- `output` and `git_export`: configuration, explicit operations, evidence paths, policy records, and read-only browser labels. No automatic export or eager root creation was found.

### Current CI and Prompt 02 gate

- Latest workflow for the authoritative SHA: GitHub Actions run `34077479576`
- Status/conclusion: `completed / failure`
- Completed: `2026-09-07T02:48:34Z`
- URL: `https://github.com/Prajnanabodhini/Database_Discovery_Tool/actions/runs/34077479576`
- The red baseline is a known Prompt 03 input. It prohibits live work but does not block the next offline remediation prompt.
- Files changed: `V3_1_1_HARDENING_REPORT.md` only.
- Behavior changed: none.
- Database access: none.
- Protected architecture: preserved.
- Unrelated tracked changes: none.
- Unresolved findings: all three P1, two P2, and two P3 items remain open.
- Next prompt: Prompt 03 is safe to start. No live prompt is authorized.

## Finding work areas

### Windows CI path identity

Local implementation and regression tests pass; the mandatory GitHub Actions gate remains pending.

- Root cause: tests compared a canonical long-form path returned by production code with an unresolved Windows temporary path that may use an 8.3 short-name alias.
- `test_runtime_self_test.py`: both the recorded subprocess cwd and expected temporary root are resolved before equality comparison.
- `test_web_app.py`: the regenerated destination, source run, generated HTML path, and output root are resolved before parent-containment and `relative_to` assertions.
- Production code was not changed because its `Path.resolve()`, `relative_to()`, output containment, and reparse-point protections are correct and must remain strict.
- No runner username, short path, drive letter, or temporary directory was hardcoded.
- Previously failing targeted tests: 2 passed in 0.88s.
- Path-containment, self-test, and report-regeneration group: 10 passed in 1.54s.
- Complete non-live suite: 159 passed, 2 skipped, 241 subtests passed in 6.90s.
- Local failures: 0.
- Existing CI baseline: run `34077479576`, Windows/Python 3.11, failed before this change.
- Candidate CI run: pending an approved commit and push.
- Database access: none.
- Live validation: not started or authorized.
- Gate decision: **PENDING** until candidate GitHub Actions completes green.
- Next prompt: **not safe to start** while this CI gate is pending.

### External and opaque view sampling

Not started.

### Git-export profile-value privacy

Not started.

### CLI report semantics

Not started.

### Inventory connection-failure lifecycle

Not started.

## Security re-audit

Not started.

## Offline regression and GitHub Actions

Not started. Initial CI is red as recorded above.

## Live validation

Not authorized or started.

## Final changed-file list

Not final. Prompt 01 adds only `V3_1_1_HARDENING_REPORT.md`.

## Residual limitations

To be completed during sequential hardening.

## Freeze decision

`NOT READY TO FREEZE`
