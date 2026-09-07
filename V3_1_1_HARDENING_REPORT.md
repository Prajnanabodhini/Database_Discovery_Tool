# SchoolERP MSSQL Documenter v3.1.1 Hardening Report

## Header

- Repository: `Prajnanabodhini/Database_Discovery_Tool`
- Starting SHA: `e2188237809efdcc324a79930640628a3975c8d6`
- Working branch: `main`
- Current hardening branch: `v3.1.1-hardening`
- Candidate implementation SHA: `1dc8825c2445342e44ee59ca609770284ffd8d3b`
- Baseline date/time: `2026-09-07T10:30:21.0332931+05:30`
- System Python: `3.11.9`
- Project `.venv` Python: `3.13.14`
- Package: `mssql-database-documenter 0.3.1`
- Initial working tree: dirty only because the complete v3.1.1 hardening prompt-pack directory is untracked; no tracked application files were modified
- Initial CI: **FAILED** for the starting SHA; GitHub Actions run `34077479576`, completed `2026-09-07T02:48:34Z`
- Initial CI URL: `https://github.com/Prajnanabodhini/Database_Discovery_Tool/actions/runs/34077479576`

## Current freeze decision

> **MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE**

The authorized Prompt 07, 09, 10, and 15 corrective cycle repaired initial
run-root containment and passed the complete local and Windows/Python 3.11 CI
gates. This decision authorizes no tag, release, deployment, database change,
or production operation.

## Authority and protected scope

- v3.1 implementation commit: `54477bbea476c4786c7285a9c8fd8075d04f13be`
- Original v3 baseline: `1c608d12d7c0f107931144dbbdc4e536865ab546`
- Executed instructions: `Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack`
- Prompts 00–15 ran strictly in numeric order with gate evidence.
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
| 03 | COMPLETE — CI GREEN | `tests/test_runtime_self_test.py`, `tests/test_web_app.py`, report | 2 targeted; 10 related; full suite 159 passed; CI PASS | Windows/Python 3.11 run `34088858063` passed. |
| 04 | COMPLETE | `profiling/sampler.py`, `profiling/__init__.py`, `profiling/stages.py`, `reporting/stages.py`, `tests/test_sampler.py`, report | 23 focused; 58 related; full suite 172 passed, 2 skipped, 247 subtests | Fail-closed local-only view eligibility; exact skip status is indexed and counted in coverage. |
| 05 | COMPLETE | `config.py`, `git_export.py`, `evidence_safety.py`, Web export/help, `.env.example`, README, tests, report | 28 focused; full suite 179 passed, 2 skipped, 247 subtests | Secure staged-copy profile-value policy and independent fail-closed verification. |
| 06 | COMPLETE | `main.py`, `cli.py`, README, operator guide, `tests/test_cli_report_semantics.py`, report | 22 focused/related, 14 subtests; full suite 186 passed, 2 skipped, 249 subtests | Live discovery and offline selected-run regeneration are now unambiguous. |
| 07 | COMPLETE — REVALIDATED | `inventory.py`, `tests/test_inventory.py`, `tests/test_path_containment.py`, report | 15 lifecycle/containment tests and 22 subtests; subsequent full suite 192 passed, 2 skipped, 251 subtests | Truthful failure evidence, collision naming, and lazy creation are preserved; initial inventory/full-run roots reject database-parent reparse points before external writes. |
| 08 | COMPLETE | `lineage/stages.py`, `Prompts/README.md`, report | Compile/import PASS; 11 focused tests passed | Duplicate decorator removed with no behavior change; every top-level prompt generation is classified by authority and supersession status. |
| 09 | COMPLETE — REVALIDATED | `tests/test_sampler.py`, `tests/test_path_containment.py`, `tests/test_inventory.py`, report | 121 targeted tests, 142 subtests passed | All v3.1.1 findings and protected guarantees include direct inventory/full-run initial-destination junction regressions and preserved collision naming. |
| 10 | COMPLETE — REVALIDATED | Report only | 98 focused passed, 2 skipped, 124 subtests; clean self-test 192 passed, 2 skipped, 251 subtests | Read-only SQL, Web controls, evidence transformations, initial/export/regeneration/comparison containment, sanitization, and clean-directory laziness re-audited; no open P0/P1 remains locally. |
| 11 | COMPLETE — CI GREEN | Report only | Compile/import PASS; 189 passed, 2 skipped, 251 subtests; self-test PASS; dry-run 35 SAFE; CI PASS | Clean local gate and Windows/Python 3.11 GitHub Actions run `34118948155` passed for implementation commit `37cf80a0d28f4fef32101fd74693607469e06103`. |
| 12 | COMPLETE — LIVE PASS | `V3_1_1_HARDENING_REPORT.md`; ignored runtime evidence under `output/` and `git_export/` | Dry-run, connection, metadata, metadata+logic, safe-profile, evidence audit, and Git-export audit PASS | DB1 only; no full-readonly, DB2, SP/job execution, external query, or database alteration. |
| 13 | COMPLETE — LIVE PASS | `V3_1_1_HARDENING_REPORT.md`; ignored runtime evidence under `output/` and `git_export/` | Dry-run, connection, metadata, metadata+logic, safe-profile, evidence audit, and Git-export audit PASS | DB2 only; identity/output isolation and absence of DB1 contamination verified. |
| 14 | COMPLETE — OFFLINE SMOKE PASS (RECONFIRMED) | `V3_1_1_HARDENING_REPORT.md`; ignored exports/regeneration/comparisons under `git_export/` and `output/` | Two complete Git export, offline report regeneration, real 2-run comparison, and real 3-run comparison cycles PASS | Authorized rerun reconfirmed source preservation, offline behavior, and export safety; no runtime evidence committed. |
| 15 | COMPLETE — READY TO FREEZE | Documentation/status updates; repaired code and regressions from Prompts 07/09 | 192 passed, 2 platform-privilege skips, 251 subtests; 35-query dry-run PASS; CI PASS | Candidate `1dc8825c2445342e44ee59ca609770284ffd8d3b`; Windows/Python 3.11 run `34141997707` completed successfully. |

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

Local implementation, regression tests, and the mandatory GitHub Actions gate pass.

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
- Candidate commit: `cfddd59156ff495e3ba84c580c2d076305212c8d`.
- Candidate CI run: `34088858063`, Windows/Python 3.11, completed successfully at `2026-09-07T05:59:32Z`.
- Candidate CI URL: `https://github.com/Prajnanabodhini/Database_Discovery_Tool/actions/runs/34088858063`.
- Database access: none.
- Live validation: not started or authorized.
- Gate decision: **PASS**.
- Next prompt: Prompt 04 is safe to start. Live validation remains unauthorized.

### External and opaque view sampling

Prompt 04 is complete. View sampling now requires a positive, metadata-backed
`ViewSampleEligibility` decision; absence of proof is not treated as proof of
safety. The restriction applies identically in `safe-profile` and
`full-readonly`, with no remote-sampling override.

Decision contract:

- Allowed status: `ELIGIBLE_LOCAL_ONLY_VIEW`.
- Denied non-error status: `SKIPPED_EXTERNAL_OR_OPAQUE_VIEW_DEPENDENCY`.
- Tables retain their existing bounded-sampling behavior and do not pass through
  the view-specific gate.
- A view is denied when its definition is unavailable/encrypted, its definition
  or static evidence is dynamic/opaque, dependency discovery failed, a
  dependency is ambiguous/caller-dependent/unresolved, a target server is
  present, another database is referenced, an external reference kind is
  present, an external synonym is used, or `OPENQUERY`, `OPENROWSET`, or
  `OPENDATASOURCE` is detected.
- A three-part reference is allowed only when its catalog unambiguously matches
  the configured current database and all other evidence remains local and
  complete.

Evidence sources are limited to data already collected by the existing
programmable-object stage: view metadata and sanitized definitions,
`sys.sql_expression_dependencies` results, static definition references,
synonym metadata, and recorded query errors. The eligibility gate creates no
connection and executes no discovery query. A source scan also found no
connection helper or direct connection call in the profiling package.

For every planned view, the exact status, structured reason codes, and evidence
sources are retained in the in-memory sample index and written to
`SAMPLE_INDEX.csv`. `DISCOVERY_COVERAGE.md` now aggregates sample-index statuses,
so skipped external/opaque views remain visible and truthful even though no
sample query or sample artifact is produced for them.

Verification:

- Focused sampler suite: 23 passed, 6 subtests passed.
- Sampling/full-run/mode-policy regression group: 58 passed, 101 subtests passed.
- Complete offline suite: 172 passed, 2 skipped, 247 subtests passed in 12.23s.
- Python compilation: PASS.
- Read-only SQL validation remains in the execution path and generated local
  view SQL is validated by regression coverage.
- Database connections: none.
- External systems are never intentionally queried. Views whose local-only
  execution cannot be proven are skipped before sample SQL execution.
- Gate decision: **PASS**.
- Next prompt: Prompt 05 is safe to start. Live validation remains unauthorized.

### Git-export profile-value privacy

Prompt 05 is complete. Canonical local output remains the useful working
evidence and is never rewritten by Git export. The temporary staged copy now
applies a separate, stricter publication policy before it can be copied into
the configured Git-export root.

Policy contract:

- `GIT_EXPORT_PROFILE_VALUE_POLICY=mask_unknown_text` is the secure default.
- The only other accepted value is `aggregate_only`; `raw` and all unknown
  values fail closed in both configuration parsing and the exporter boundary.
- `mask_unknown_text` pseudonymizes unknown string-like minima, maxima, and
  low-cardinality values; applies existing sensitive-category masking; redacts
  credentials and binary values; preserves only explicitly operator-reviewed
  `Non-sensitive` labels; and may retain non-sensitive numeric/date structural
  extrema.
- `aggregate_only` blanks value-bearing extrema and distribution labels in the
  staged copy while retaining counts, percentages, status, type, and aggregate
  metrics.
- Sample payload policy remains separately controlled by
  `GIT_EXPORT_SAMPLE_POLICY`.

`99_Git_Handoff/GIT_EXPORT_POLICY.json` and the staged manifest now record
`profile_value_policy`, `profile_values_masked`, `profile_values_omitted`, the
aggregate-only withholding marker, and `source_evidence_mutated: false`. The
staged manifest file list and SHA-256 checksums are regenerated only after
profile and sample policy transformations.

The independent evidence audit does not trust those claims alone. For a staged
export it requires the policy record, verifies that it matches the manifest,
checks the staged profile cells against the declared policy and sensitivity
evidence, validates the masked-value counter, and fails if unknown text,
unredacted binary data, sensitive values, or aggregate-only payload fields are
present. A regression test deliberately reintroduces raw unknown text after
export and confirms that the independent audit fails.

Documentation now distinguishes canonical local evidence from the stricter
Git-safe staged copy in `.env.example`, the README, dashboard, and Help page.
Git-export protection is described as a conservative publication boundary, not
as proof that all local evidence is semantically de-identified.

Verification:

- Focused configuration/export/audit suite: 28 passed.
- Related export/containment/Web suite: 50 passed, 2 skipped, 15 subtests passed.
- Complete offline suite: 179 passed, 2 skipped, 247 subtests passed in 7.05s.
- Python compilation: PASS.
- Source profile evidence hash/bytes unchanged by export: PASS.
- Staged manifest policy and checksums: PASS.
- Database connections: none.
- Gate decision: **PASS**.
- Next prompt: Prompt 06 is safe to start. Live validation remains unauthorized.

### CLI report semantics

Prompt 06 is complete. The ambiguous legacy CLI `report` command has been
removed from help and dispatch. Operators now have distinct commands whose
names and help text state whether MSSQL will be contacted.

Command contract:

- `all` remains unchanged: it performs a new live read-only discovery and
  generates that run's normal reports.
- `discover-and-report` is an explicit alias for the same new live read-only
  discovery path.
- `regenerate-reports --run <path-or-output:reference>` loads one existing
  manifested run under the configured `OUTPUT_ROOT` and calls the existing
  `report_regeneration.py` service without importing or calling a connection
  path.
- Both an absolute/relative contained run path and an
  `output:<database/run_directory>` reference are accepted. Traversal,
  out-of-root sources, missing paths, and unmanifested directories fail closed.
- The top-level `main.py` launcher exposes and forwards the same offline
  regeneration operation.

The offline command creates a unique versioned directory below
`output/report_regenerations/<database>/<run>/`, preserves source hashes,
produces a regeneration manifest and checksums, and prints sanitized JSON that
explicitly records `database_connection_attempted: false` and
`canonical_source_mutated: false`.

README and `OPERATOR_RUN_GUIDE.md` now show separate live discovery and offline
regeneration examples and state that the former `report` command is not
accepted. CLI help is also verified from a clean temporary working directory;
it creates neither `output/` nor `git_export/`.

Verification:

- CLI/regeneration/launcher/Web group: 22 passed, 14 subtests passed.
- Complete offline suite: 186 passed, 2 skipped, 249 subtests passed in 8.05s.
- Python compilation: PASS.
- Patched MSSQL connection function called during regeneration: no.
- Canonical source hashes before/after: unchanged.
- Versioned destination containment: PASS.
- Existing `all` discovery dispatch: unchanged and covered.
- Existing Web regeneration: unchanged and covered.
- Database connections: none.
- Gate decision: **PASS**.
- Next prompt: Prompt 07 is safe to start. Live validation remains unauthorized.

### Inventory connection-failure lifecycle

Prompt 07 is complete using preferred solution A. Immediately after
`run_inventory()` reserves a unique run root, it writes the minimum recoverable
control set before calling the connection function:

- `RUN_CONFIGURATION.json` with sanitized resolved metadata-mode settings;
- `STAGE_STATUS.json` with connection and metadata lifecycle state;
- `run_summary.json` with `INITIALIZING`, zero completed stages, and `0/2`
  coverage;
- `manifest.json` with the same truthful status and file inventory;
- header-only `DISCOVERY_ERRORS.csv`;
- refreshed `checksums.sha256`.

After connection succeeds, the controls advance to `RUNNING`, with connection
`PASS` and metadata `RUNNING`. Normal completion finalizes as `COMPLETED` or
`COMPLETED_WITH_WARNINGS`, retaining the existing two completed stages and the
existing metadata artifact behavior.

If the initial connection fails, the reserved run is retained as truthful
diagnostic evidence rather than becoming an unmanifested orphan. Its summary
and manifest are `FAILED`, completion is `0/2`, connection is `FAILED`, metadata
is `NOT_STARTED`, the sanitized failure is recorded in `DISCOVERY_ERRORS.csv`,
and checksums are regenerated. The raised operator-facing exception is also
sanitized. No disabled-security or metadata catalogue artifact is written
before connection establishment, and no metadata-completed claim is made.

If a handled failure occurs after connection establishment, the same mechanism
finalizes a truthful `PARTIAL` run with connection recorded as complete and
metadata failed. The implementation never deletes a run or a pre-existing
directory; unique-name reservation and sanitized database path components
preserve containment under the configured output root.

Independent metadata query failures retain their prior semantics: the affected
CSV is header-only, the error is a warning, other queries continue, and the run
finishes `COMPLETED_WITH_WARNINGS`.

Verification:

- Inventory/metadata focused suite: 17 passed, 59 subtests passed.
- Complete offline suite: 189 passed, 2 skipped, 249 subtests passed in 8.85s.
- Python compilation: PASS.
- Initial control manifest present before connection invocation: PASS.
- Simulated initial connection failure: manifested `FAILED`; no orphan.
- Secrets in raised exception or retained evidence: none.
- Failed-run manifest/checksums: present and valid.
- Pre-existing directory content/hash: unchanged.
- Run-root containment: PASS.
- Successful inventory behavior: PASS.
- Query-level header-only warning behavior: PASS.
- Database connections: none; connection behavior was simulated.
- Gate decision: **PASS**.
- Next prompt: Prompt 08 is safe to start. Live validation remains unauthorized.

### Code and prompt governance cleanup

Prompt 08 made only the two authorized P3 cleanup changes. The duplicate
consecutive `@staticmethod` on `LineageStagesMixin._programmable_headers` was
reduced to one decorator; the helper body and all unrelated lineage logic are
unchanged.

`Prompts/README.md` now classifies every top-level prompt generation. The v2
pack, repair/layman UI plan, v3 pack, v3 sequential execution record, and v3.1
remediation pack are explicitly historical and cannot be executed now. The
v3.1.1 hardening pack is the sole active authority, remains sequential and
authorization-gated, and must be reclassified as `EXECUTED / HISTORICAL` after
its final fine-comb and freeze gate. Historical prompts remain retained as
evidence and cannot be used to revert the current architecture.

Verification:

- Repository virtual environment: Python 3.13.14.
- Python compilation of `main.py`, `src`, and `tests`: PASS.
- Corrected lineage module import/helper smoke check: PASS.
- Focused lineage suite: 11 passed in 0.32s.
- Top-level prompt-generation index coverage: PASS; no unclassified item.
- Duplicate consecutive `@staticmethod` scan: PASS; no match remains.
- Functional behavior changes: none.
- Database connections: none.
- Gate decision: **PASS**.
- Next prompt: Prompt 09 is safe to start. Live validation remains unauthorized.

### Targeted v3.1.1 regression suite

Prompt 09 is complete. Existing behavioral regressions already covered every
finding family except that encrypted and opaque view flags were only covered
indirectly by the broader unavailable/dynamic fail-closed cases. The sampler
test now explicitly includes `is_encrypted` and `definition_opaque` inputs.
No production code or safety boundary changed.

Finding-to-test regression matrix:

| Finding | Test file | Test name(s) | Result |
|---|---|---|---|
| Self-test cwd identity and Windows short/long aliases | `tests/test_runtime_self_test.py` | `test_explicit_self_test_uses_fixed_argv_without_shell_or_runtime_roots` | PASS |
| Report-regeneration containment and Windows short/long aliases | `tests/test_web_app.py` | `test_report_regeneration_is_run_selected_offline_and_source_preserving` | PASS |
| Reparse/junction containment | `tests/test_path_containment.py` | `test_shared_guard_rejects_real_reparse_point_before_descending`; Git-export, comparison-export, and report-regeneration nested-reparse tests | 4 PASS |
| Initial inventory/full-run destination containment | `tests/test_path_containment.py` | `test_initial_run_root_rejects_database_parent_reparse_without_external_write`; `test_sequential_run_rejects_database_parent_reparse_without_external_write` | PASS |
| Additional browser/export symlink containment | `tests/test_file_browser.py` | `test_symlink_escape_is_blocked_when_supported`; `test_git_export_rejects_symlinks_when_supported` | 2 SKIPPED: this Windows identity cannot create symlinks; equivalent junction guards passed |
| Local view allowed | `tests/test_sampler.py` | `test_local_only_view_is_sample_eligible`; `test_current_database_three_part_view_reference_is_allowed` | PASS |
| Cross-database view denied | `tests/test_sampler.py` | `test_other_database_view_reference_is_denied` | PASS |
| Linked-server view denied | `tests/test_sampler.py` | `test_linked_server_view_reference_is_denied` | PASS |
| External view constructs denied | `tests/test_sampler.py` | `test_openquery_view_is_denied`; `test_openrowset_view_is_denied`; `test_opendatasource_view_is_denied`; `test_external_synonym_view_reference_is_denied` | PASS |
| Unavailable, encrypted, opaque, dynamic, dependency-failed, and unresolved views denied | `tests/test_sampler.py` | `test_unavailable_encrypted_opaque_dynamic_and_unresolved_view_evidence_fails_closed` | PASS, 6 subtests |
| Table sampling unaffected | `tests/test_sampler.py` | `test_table_sampling_is_unaffected_without_view_evidence` | PASS |
| Unknown text extrema and low-cardinality text masked | `tests/test_git_export_policy.py` | `test_default_profile_policy_masks_unknown_sensitive_and_binary_values`; `test_independent_audit_rejects_raw_unknown_text_despite_policy_claim` | PASS |
| Known PII and credentials protected | `tests/test_git_export_policy.py`, `tests/test_evidence_safety.py` | default profile-policy test; `test_raw_sensitive_profile_values_fail_closed`; `test_masked_sensitive_profile_values_pass` | PASS |
| Explicit Non-sensitive values allowed | `tests/test_git_export_policy.py` | `test_default_profile_policy_masks_unknown_sensitive_and_binary_values` | PASS |
| Aggregate-only profile publication | `tests/test_git_export_policy.py` | `test_aggregate_only_removes_payloads_and_retains_aggregate_metrics` | PASS |
| Git profile manifest and checksums accurate | `tests/test_git_export_policy.py` | `test_profile_policy_manifest_counters_and_checksums_are_accurate` | PASS |
| Git export does not mutate source | `tests/test_git_export_policy.py`, `tests/test_evidence_safety.py` | default/masked-only source-hash tests; `test_git_export_sanitizes_raw_profile_value_without_mutating_source` | PASS |
| CLI help semantics | `tests/test_cli_report_semantics.py` | `test_help_distinguishes_live_discovery_from_offline_regeneration_without_roots`; `test_legacy_report_command_is_not_accepted` | PASS |
| CLI all/discover semantics | `tests/test_cli_report_semantics.py` | `test_all_discovery_dispatch_is_unchanged_and_alias_is_explicit` | PASS, 2 subtests |
| Offline regeneration, containment, and no DB connection | `tests/test_cli_report_semantics.py` | `test_offline_cli_regeneration_is_contained_versioned_and_source_preserving`; out-of-root and unmanifested-source rejection tests | PASS |
| Initial inventory connection failure, truthful lifecycle, and no orphan | `tests/test_inventory.py` | `test_initial_connection_failure_retains_sanitized_manifested_failed_run` | PASS |
| SQL validator | `tests/test_safety.py`, `tests/test_fullrun.py` | registered-query safety, forbidden-operation rejection, and static-query gate tests | PASS |
| Cursor proxy | `tests/test_safety.py` | `test_cursor_revalidates_at_execution_boundary`; `test_executemany_is_never_available`; `test_unknown_cursor_capabilities_are_fail_closed` | PASS |
| SQL Agent no-execution | `tests/test_agent_lineage.py` | `test_agent_query_remains_select_only_and_raw_command_is_internal`; `test_analyzer_source_contains_no_execution_primitives` | PASS |
| Discovery mode distinctions | `tests/test_mode_policy.py` | `test_four_modes_have_truthful_distinct_contracts`; `test_safe_and_full_profile_take_different_runtime_branches`; exact-count ceiling tests | PASS |
| Sensitivity reconciliation | `tests/test_fullrun.py`, `tests/test_sensitivity.py` | `test_final_sample_classification_remasks_earlier_profile_evidence`; override and extended-property evidence tests | PASS |
| Git sample exclusion | `tests/test_git_export_policy.py` | `test_default_excludes_payload_but_retains_control_evidence`; `test_masked_only_sanitizes_copy_without_mutating_source` | PASS |
| Three-run comparison timeline | `tests/test_comparison.py` | `test_three_run_timeline_numeric_deltas_and_definition_diff`; `test_all_required_three_run_timeline_patterns`; multi-event timeline test | PASS |
| Web CSRF and loopback | `tests/test_web_app.py` | `test_app_is_lazy_loopback_only_and_has_security_headers`; `test_csrf_action_allowlist_invalid_database_and_dry_run` | PASS |
| Path containment | `tests/test_path_containment.py`, `tests/test_file_browser.py`, `tests/test_cli_report_semantics.py` | shared guard, traversal, reparse, and out-of-root regeneration tests | PASS; 2 additional symlink cases environment-skipped |
| Lazy runtime roots | `tests/test_web_app.py`, `tests/test_file_browser.py`, `tests/test_inventory.py` | import/missing-root non-creation and stage-lazy run-root tests | PASS |
| Runtime pytest decoupling | `tests/test_runtime_self_test.py` | `test_live_run_review_never_invokes_pytest_or_subprocess`; explicit developer self-test tests | PASS |
| MSSQL metadata completeness | `tests/test_metadata_completeness.py` | required-family registration, contract, support-state, runner, privacy, and comparison-registration tests | PASS |

Verification:

- Targeted sampler suite after explicit encrypted/opaque cases: 23 passed,
  8 subtests passed in 0.69s.
- Complete targeted v3.1.1 suite: 163 passed, 2 skipped, 228 subtests passed
  in 13.00s; 165 tests collected.
- Skip audit: only the two existing Windows symlink-creation privilege cases;
  all four real junction/reparse containment tests passed.
- Prohibited database connections: none; connection-sensitive tests use
  fail-fast mocks.
- Production files changed by Prompt 09: none.
- Gate decision: **PASS**.
- Next prompt: Prompt 10 is safe to start. Live validation remains unauthorized.

## Security and Read-Only Re-audit

Prompt 10 is complete. The post-implementation source, test, and runtime audit
found no new P0 or P1 issue and required no production-code change.

### Database execution boundary

- All 35 registered query specifications across base, metadata, optional
  security metadata, programmable-object, and SQL Agent metadata families pass
  the fail-closed validator.
- Six production `.execute()` callsites exist. The CLI connection check,
  inventory, two full-run fetch paths, and Web connection check all operate on
  `ReadOnlyCursor`; the sixth is the proxy's single underlying-cursor delegate
  after immediate validation.
- The only `executemany` surface is `ReadOnlyCursor.executemany`, which always
  raises `UnsafeSqlError`.
- DML, DDL, administration, stored-procedure invocation, SQL Agent execution,
  sequence advancement, multiple statements, and external query primitives
  remain validator-denied. Matches elsewhere are deny-list definitions or
  static parsers that classify discovered text without executing it.
- The connection string retains `ApplicationIntent=ReadOnly`; autocommit is
  disabled, and every connection closes through rollback.
- There are zero `eval()` or `exec()` callsites. The one
  `compile(content, path, "exec")` occurrence compiles repository Python for
  syntax validation and never evaluates the returned code object.
- The sole production subprocess facility is the explicit developer
  `self-test`, with fixed pytest arguments, `shell=False`, a timeout, and no
  discovery configuration or connection path.

### Web boundary

- Configuration and request processing both enforce loopback hosts.
- Every state-changing request passes same-origin and constant-time CSRF-token
  validation.
- Job actions, databases, discovery modes, and comparison categories are
  allowlisted. No endpoint accepts SQL, shell text, an executable, or a
  user-selected subprocess command.
- The Web package contains zero subprocess, `Popen`, `os.system`, or
  `shell=` surface. Optional browser opening uses only the configured
  loopback URL.
- File, run, comparison, export, and regeneration inputs resolve through
  configured-root containment. Absolute paths, traversal, escaped symlinks,
  and destination reparse points fail closed.
- `JobManager` holds one current heavy job under a lock and rejects another
  non-final job with the `JobConflictError` exception.

### Evidence boundary

- Configuration serialization, job logs, exceptions, inventory failures, and
  connection-check results sanitize configured secrets, server identity, and
  login identity.
- Raw sample Git export remains invalid. The default excludes payloads, while
  the only alternate sample mode sanitizes a staged copy.
- Git profile publication accepts only `mask_unknown_text` or
  `aggregate_only`; unknown text, sensitive values, credentials, and binary
  values remain fail-closed according to the selected staged policy.
- Git export applies transformations to a temporary copy, refreshes its
  manifest and checksums, runs an independent evidence audit, and only then
  copies to a contained destination.
- Git export and report-regeneration regression hashes prove canonical source
  runs are not mutated. Regeneration also verifies its source inventory before
  committing a versioned contained destination.
- Exact tracked credential/key filename scan: zero. `.env` remains ignored;
  the tracked `.env.example` is the credential-free template.

### Runtime laziness and verification

A newly created OS-temporary working directory was used for each smoke step.
After import, top-level help, Flask app construction, and the actual explicit
self-test, both `output/` and `git_export/` remained absent. The temporary
directory target was canonicalized, validated under the OS temp root, and
removed after the audit. The repository's existing runtime roots remain
Git-ignored and were not added to the working tree.

- Focused read-only/Web/evidence/containment/laziness suite: 110 passed,
  2 skipped, 40 subtests passed in 6.42s.
- Actual explicit self-test: 189 passed, 2 skipped, 251 subtests passed in
  7.63s; status `PASS`, connection attempted `false`, runtime root created
  `false`.
- The two skips are the existing Windows symlink-creation privilege cases. All
  real junction/reparse containment tests pass.
- Import/help/Web-construction clean-directory checks: PASS.
- Database or external-system connections during Prompt 10: none.
- Newly discovered P0/P1 findings: none.
- Gate decision: **PASS**.
- Next prompt: Prompt 11 is safe to start. Live validation remains unauthorized.

## Offline regression and GitHub Actions

Prompt 11 is complete. The clean local acceptance gate and the mandatory
Windows/Python 3.11 GitHub Actions gate both passed.

Clean-start handling:

- `.env` has zero tracked entries and remains ignored.
- Existing ignored `output/` (9,381 files, 223,597,693 bytes) and
  `git_export/` (4,401 files, 55,568,852 bytes) were moved into a unique,
  canonicalized holding directory inside the repository before the gate.
- Twelve project cache directories were removed before execution. The virtual
  environment was explicitly excluded.
- Every command was checked immediately for runtime-root creation.
- Ten caches created by compilation/import/test execution were removed after
  the gate.
- The original runtime evidence was restored with exactly the same file counts
  and aggregate byte sizes. The empty holding directory was then removed.

Local command results using the repository Python 3.13.14 virtual environment:

- `python -m compileall -q main.py src`: PASS.
- Required import command for `main`, the package, report regeneration, and
  the Web app module: PASS.
- `python -m pytest -q -p no:cacheprovider -m "not live" tests`: 189 passed,
  2 skipped, 251 subtests passed in 8.22s; zero failures.
- `python main.py self-test`: PASS; inner suite 189 passed, 2 skipped,
  251 subtests passed in 7.13s; connection attempted `false`; runtime root
  created `false`.
- Package CLI dry-run registry validation: PASS; all 35 registered queries
  `SAFE`, connection attempted `false`, runtime roots created `false`.
- The two skips remain only the Windows symlink-creation privilege cases; real
  junction/reparse tests pass.
- Live MSSQL or external-system connections: none.

CI gate:

- Current branch: `v3.1.1-hardening`.
- CI-validated implementation commit:
  `37cf80a0d28f4fef32101fd74693607469e06103`.
- Workflow: `Offline developer quality gate`, run `34118948155`,
  <https://github.com/Prajnanabodhini/Database_Discovery_Tool/actions/runs/34118948155>.
- Job: `Windows / Python 3.11 / offline` on `windows-latest`.
- Status/conclusion: `completed / success`.
- Gate decision: **PASS — PROMPT 11 COMPLETE**.
- Prompt 12 is safe to start only with explicit live-DB1 authorization. No live
  validation was started by Prompt 11.

## Live validation

### Prompt 12 — DB1 read-only validation

Prompt 12 is complete. The user explicitly authorized DB1, and the required
steps were executed sequentially only after Prompt 11's local and GitHub
Actions gates were green. Only the first configured database was selected.
Database, server, login, object, and sampled data values are not copied into
this report.

Connection and read-only controls:

- Dry-run: PASS; all 35 registered query families were classified `SAFE`,
  `connection_attempted=false`.
- Test connection: PASS; three predefined metadata query families executed.
  Displayed server and login values were sanitized/redacted.
- The database reported `ONLINE` and is not globally marked read-only.
  Application safety remained enforced through `ApplicationIntent=ReadOnly`,
  the guarded query validator/cursor, disabled autocommit, and rollback.
- No full-readonly mode, second database, stored procedure, SQL Agent job,
  external system, or database-altering operation was executed.

Live runs:

| Mode | Run ID | Status | Evidence result |
|---|---|---|---|
| metadata | `20260907_120858` | `COMPLETED` | 14 stages PASS, 6 skipped by mode, 159 files, 158 valid checksums, zero warnings/errors, profiles, or sample payloads |
| metadata+logic | `20260907_121315` | `COMPLETED` | 17 stages PASS, 3 skipped by mode, 986 files, 985 valid checksums, zero warnings/errors, profiles, or sample payloads |
| safe-profile | `20260907_121708` | `COMPLETED_WITH_WARNINGS` | 20 stages PASS, 1 contained object-level sampling warning, 1,060 files, 1,059 valid checksums |

Metadata+logic evidence included 2 views, 809 procedures, 11 functions,
2,545 dependency records, 4,651 lineage edges, 821 pipelines, 3 SQL Agent
jobs, and 4 agent references. No raw SQL Agent command was persisted.

Safe-profile evidence contained 795 column-profile rows, 3,818
low-cardinality rows, 806 sensitivity rows, 806 masking rows, and 74 bounded
sample records/files. Of those records, 62 user tables and 1 view were
sampled, 10 user tables were empty, and 1 view was inaccessible at query time.
That view produced a contained `ProgrammingError`: it was marked
`INACCESSIBLE`, skipped at object level, and the stage continued. The run
had no failed stage.

The persisted view catalogue and dependency/reference evidence were evaluated
offline with the production eligibility evaluator: both discovered views were
local-only and sample-eligible. One was sampled; the other was the inaccessible
view described above. The evidence included 114 external-reference records,
but none claimed an external query.

`NOT PRESENT IN DB1 — regression test is authoritative`

No cross-database, external, encrypted, dynamic, or otherwise opaque view was
present in DB1. Therefore no external system was contacted to prove a skip;
the mandatory regression test remains the authority for that branch.

Evidence-safety audit:

- PASS across all 1,060 source-evidence files.
- 806 classified columns and 162 sensitive columns were reviewed; 11,539
  sensitive values were checked.
- Forbidden files, transient paths, configured secrets, unredacted secret
  assignments, unmasked profile values, and sample-value violations: zero.
- All eight evidence-safety checks passed; total violations: zero.

Explicit Git-export staging/audit:

- Exported only from safe-profile run `20260907_121708`; the source evidence
  remained unchanged.
- 987 staged files; all 986 checksum entries validated.
- Default sample policy: `exclude`; raw sample payload CSV files staged: zero.
- Unknown-text profile-value policy: `mask_unknown_text`; 2,360 values were
  masked and zero were omitted.
- Configured secret/server/login-string findings: zero.
- Independent Git-export evidence audit: `PASS`, zero violations.

Gate decision: **PASS — PROMPT 12 COMPLETE**.

Prompt 13 was separately authorized and is recorded below.

### Prompt 13 — DB2 read-only validation

Prompt 13 is complete. It started only after Prompt 12 fully passed and the
user explicitly authorized the second configured database. Exactly that
database was selected in memory for every step. Database, server, login,
object, and sampled data values are not copied into this report.

Connection and read-only controls:

- Dry-run: PASS; all 35 registered query families were classified `SAFE`,
  `connection_attempted=false`.
- Test connection: PASS; three predefined metadata query families executed,
  with server and login fields sanitized/redacted.
- The database reported `ONLINE` and is not globally marked read-only.
  Application safety remained enforced through `ApplicationIntent=ReadOnly`,
  the guarded query validator/cursor, disabled autocommit, and rollback.
- No full-readonly mode, first-database discovery, stored procedure, SQL Agent
  job, external system, comparison, or database-altering operation was
  executed.

Live runs:

| Mode | Run ID | Status | Evidence result |
|---|---|---|---|
| metadata | `20260907_123808` | `COMPLETED` | 14 stages PASS, 6 skipped by mode, 270 files, 269 valid checksums, zero warnings/errors, profiles, or sample payloads |
| metadata+logic | `20260907_124007` | `COMPLETED` | 17 stages PASS, 3 skipped by mode, 1,102 files, 1,101 valid checksums, zero warnings/errors, profiles, or sample payloads |
| safe-profile | `20260907_124647` | `COMPLETED_WITH_WARNINGS` | 20 stages PASS, no failed stage, 1 contained object-level sampling warning, 1,287 files, 1,286 valid checksums |

Metadata+logic evidence included 183 tables, 2 views, 814 procedures,
11 functions, 2,495 dependency records, 4,906 lineage edges, 826 pipelines,
3 SQL Agent metadata records, and 4 agent references. SQL Agent metadata is
deliberately server-global; it was classified separately from primary DB2
identity evidence. No raw SQL Agent command was persisted.

Database isolation and generic behavior:

- The output directory parent, manifest identity, run-summary identity, and
  resolved mode policy matched DB2 in every run.
- Primary database-identity records belonging to another database: zero.
- Exact DB1 value occurrences in DB2 CSV evidence: zero.
- DB2 output and Git-export roots were separately contained; DB1 evidence was
  neither read into nor written into the DB2 runs.
- The metadata+logic independent evidence audit passed with zero violations.

Safe-profile evidence contained 2,078 column-profile rows, 6,105
low-cardinality rows, 2,089 sensitivity rows, 2,089 masking rows, and 185
bounded sample records/files. Of those records, 105 user tables and 1 view
were sampled, 78 user tables were empty, and 1 view was inaccessible. The
inaccessible view produced a contained `ProgrammingError`; it was recorded
as `INACCESSIBLE`, skipped at object level, and the stage continued.

The persisted DB2 view catalogue and dependency/reference evidence were
re-evaluated offline with the production eligibility evaluator. Both views
were local-only and sample-eligible. One sampled successfully and the other
was the inaccessible view described above. No cross-database, external,
encrypted, dynamic, or otherwise opaque view was present:

`NOT PRESENT IN DB2 — regression test is authoritative`

The evidence contained 114 external-reference records, all representing
static metadata. Records claiming an external query: zero. No external system
was contacted to test the skip rule.

Evidence-safety audit:

- PASS across all 1,287 source-evidence files.
- 2,089 classified columns and 287 sensitive columns were reviewed; 12,572
  sensitive values were checked.
- Forbidden files, transient paths, configured secrets, unredacted secret
  assignments, unmasked profile values, and sample-value violations: zero.
- All eight evidence-safety checks passed; total violations: zero.

Git-export safety check:

- Exported only safe-profile run `20260907_124647`; all 1,287 source files
  remained unchanged.
- 1,103 staged files; all 1,102 checksum entries validated.
- Default sample policy: `exclude`; raw sample payload CSV files staged: zero.
- Generic unknown-text profile-value policy: `mask_unknown_text`; 3,091
  profile values were masked and zero were omitted.
- DB1/configured secret/server/login-string findings: zero.
- Staged manifest identity and contained export root matched DB2.
- Independent Git-export evidence audit: `PASS`, zero violations.

Gate decision: **PASS — PROMPT 13 COMPLETE**.

Prompt 14 was separately authorized and is recorded below.

### Prompt 14 — Git export, offline report, and comparison smoke

Prompt 14 is complete. Its work used existing manifested evidence only. The
report-regeneration and comparison connection entrypoint was patched
fail-closed during execution and was never called. No new live discovery,
stored procedure, SQL Agent job, external-system query, or database mutation
occurred.

#### A. Default Git export

- Approved source: DB2 metadata+logic run `20260907_124007`.
- All 1,102 source-file hashes remained unchanged.
- The new isolated export contains 1,103 files; all 1,102 independently
  recalculated checksum entries are valid.
- Manifest and independent Git-export policy record agree.
- Sample policy: `exclude`; raw sample payloads exported: zero.
- Profile-value policy: `mask_unknown_text`. This metadata+logic source
  contained no profile values, so the truthful masked count is zero.
- Configured server/login/secret findings: zero.
- Independent export audit: `PASS`, zero violations.

#### B. Offline report regeneration

- Canonical source: DB2 safe-profile run `20260907_124647`.
- Versioned destination:
  `regen_20260907_130516_834233_4319cc89`.
- Database connection attempted: `false`.
- All 1,287 canonical source-file hashes remained unchanged.
- The separate destination contains Markdown, static HTML, regeneration
  manifest, and checksums; all 3 checksum entries are valid.
- Both Markdown and HTML rendered through the safe file renderer.
- The HTML contains no script element, JavaScript URL, or inline event
  attribute.
- Configured server/login/secret findings: zero.

#### C. Real two-run comparison

- Runs A/B: `20260906_150721` and `20260907_121315`.
- Both are real runs from the same database in `metadata+logic` mode;
  compatibility warnings: zero.
- Versioned export: `compare_20260907_130859_576436`.
- Source hashes remained unchanged; database connection attempted: `false`.
- Global comparison rows: 11,882. Primary results: 11,881 `UNCHANGED`,
  1 `CHANGED`, 0 `ADDED`, and 0 `REMOVED`. The zero add/remove counts are
  the truthful result for these snapshots.
- Numeric-delta fields: 3,254; definition-diff intervals: 1.
- Global and per-category summary arithmetic reconciles exactly.
- Explicit JSON, CSV, and static HTML exports exist; CSV rows: 11,882.
- The exported HTML is parseable and contains the comparison evidence with
  zero scripts, JavaScript URLs, or inline event attributes.

#### D. Real three-run comparison

- Chronological runs A/B/C: `20260906_150721`,
  `20260907_015059`, and `20260907_121315`.
- All three are real runs from the same database in `metadata+logic` mode;
  compatibility warnings: zero.
- Versioned export: `compare_20260907_131612_675090`.
- Source hashes remained unchanged; database connection attempted: `false`;
  source raw sample payloads: zero.
- Every comparison row contains A→B, B→C, and A→C interval results.
  Across 11,882 rows there are 35,644 `UNCHANGED` and 2 `CHANGED`
  interval occurrences.
- Timeline events: `CHANGED_B_TO_C=1`; `ADDED_IN_B=0`,
  `ADDED_IN_C=0`, `REMOVED_IN_B=0`, `REMOVED_IN_C=0`,
  `CHANGED_A_TO_B=0`, `REVERTED_TO_A=0`, and `CHANGED_BOTH=0`.
  Zero-result event classes were retained and verified rather than
  fabricating changes absent from the real evidence.
- Full-history filters for added, removed, changed-only, reverted-to-A, and
  changed-both matched independently recomputed status-token truth for every
  row.
- Numeric-delta fields: 3,254; definition-diff intervals: 2.
- The global summary equals the sum of all displayed/exported category rows,
  and every category summary also reconciles.
- Explicit JSON, CSV, and static HTML exports exist; CSV rows: 11,882.
- Static HTML includes full evidence and summary sections with zero scripts,
  JavaScript URLs, or inline event attributes.
- Configured server/login/secret findings across both comparison exports:
  zero. No raw samples or PII were copied into this report.

#### Authorized Prompt 14 rerun

Prompt 14 was run a second time on explicit user instruction. The rerun used
new source/export selections where possible and created only new versioned
destinations; it did not overwrite the first smoke-cycle evidence.

- Git export source: approved DB2 metadata run `20260907_123808`.
  All 270 source hashes remained unchanged. The export contains 271 files,
  all 270 checksum entries validate, policies are `exclude` and
  `mask_unknown_text`, raw sample payloads are zero, and the independent
  audit passed with zero violations.
- Offline report source: approved DB1 safe-profile run
  `20260907_121708`. Versioned destination:
  `regen_20260907_132428_027915_432a1c72`. No connection was attempted,
  all 1,060 source hashes remained unchanged, all 3 generated checksum entries
  validate, and Markdown/static HTML rendering passed.
- Two-run comparison: compatible DB2 metadata+logic runs
  `20260907_015735` and `20260907_124007`. Versioned export:
  `compare_20260907_132531_225470`. All 15,490 rows reconcile:
  15,489 `UNCHANGED`, 1 `CHANGED`, and truthful zero `ADDED`/`REMOVED`
  rows. It contains 8,328 numeric-delta fields and 1 definition-diff
  interval.
- Three-run comparison: chronological compatible DB1 metadata+logic runs
  `20260906_150721`, `20260907_015059`, and
  `20260907_121315`. Versioned export:
  `compare_20260907_132647_275130`. All 11,882 global/category rows
  reconcile, every A→B/B→C/A→C interval is present, all required full-history
  filters match independently recomputed truth, and zero-result timeline
  classes remain explicit. It contains 3,254 numeric-delta fields and 2
  definition-diff intervals.
- Both comparison rerun exports contain JSON, CSV, and parseable static HTML.
  Script elements, JavaScript URLs, inline event attributes, raw sample source
  payloads, and configured server/login/secret findings: zero.
- Database connections during report regeneration and both comparisons:
  zero. All canonical comparison/regeneration source hashes remained
  unchanged.

Rerun gate decision: **PASS — PROMPT 14 RECONFIRMED**.

Gate decision: **PASS — PROMPT 14 COMPLETE**.

Prompt 15 was not started at that original Prompt 14 checkpoint.

## Reopened targeted remediation

### Prompt 07 rerun — initial run-root containment

A later independent audit found one uncovered reparse-point path: the shared
`_new_run_directory()` helper created `OUTPUT_ROOT/<database>/run_<id>`
without applying the established destination guard. A pre-existing junction
at the database-parent component could therefore redirect initial inventory
or full-run evidence outside `OUTPUT_ROOT`.

The repair now:

- validates and creates the database-parent directory one component at a time
  through `ensure_contained_directory()`;
- rejects symbolic links, junctions, and other reparse points before reserving
  a run;
- uses no-follow existence checks for candidate-name collisions;
- revalidates the created run directory as contained before returning it;
- preserves lazy creation, collision suffixes, and immediate truthful
  inventory control evidence.

Files changed:

- `src/mssql_database_documenter/inventory.py`
- `tests/test_path_containment.py`
- `V3_1_1_HARDENING_REPORT.md`

Verification:

- Inventory lifecycle, collision naming, and real reparse-point containment: 15 passed,
  22 subtests passed.
- Complete offline suite: 190 passed, 2 skipped, 251 subtests passed.
- The two skips remain the Windows symlink-creation privilege cases; all real
  junction tests, including initial run-root creation, pass.
- Database connections: none.
- Prompt 07 rerun gate: **PASS**.
- Next authorized prompt: Prompt 09.

### Prompt 09 rerun — permanent regression coverage

The targeted suite now exercises the repaired shared run-root helper through
both public runtime paths:

- direct metadata/inventory run reservation rejects a real database-parent
  junction before creating anything in its target;
- `SequentialRun`, used by complete discovery and staged commands, rejects
  the same condition before any evidence or database work;
- the existing Git-export, comparison-export, report-regeneration, file
  browser, SQL, Web, privacy, mode, Agent, metadata, and comparison
  regressions remain unchanged.

Files changed:

- `tests/test_path_containment.py`
- `V3_1_1_HARDENING_REPORT.md`

Verification:

- Complete targeted hardening matrix: 121 passed, 142 subtests passed.
- Real junction containment tests: PASS.
- Database connections: none.
- Prompt 09 rerun gate: **PASS**.
- Next authorized prompt: Prompt 10.

### Prompt 10 rerun — security and evidence boundary

The focused re-audit included the repaired initial discovery path rather than
relying only on export/regeneration containment.

- All 53 production Python files parse.
- All six production `.execute()` sites remain behind `ReadOnlyCursor`
  validation, including the proxy's final delegate.
- All 35 registered SQL specifications pass the fail-closed validator.
- `ApplicationIntent=ReadOnly`, disabled autocommit, rollback/close, Agent
  no-execution, and external-query primitive denial are unchanged.
- Module-scope directory creation, `eval()`, `exec()`, `shell=True`, and
  duplicate decorators: zero.
- The only production subprocess remains the explicit fixed-argument,
  `shell=False` developer self-test.
- The Web loopback, same-origin, CSRF, action/database allowlists, single-job
  lock, and file containment tests pass.
- Git staged-copy privacy, independent evidence audit, source preservation,
  manifest/checksum refresh, and offline report regeneration tests pass.

Verification:

- Focused security/evidence/containment suite: 98 passed, 2 skipped,
  124 subtests passed.
- Clean disposable tracked working tree: help PASS; import/Web construction
  PASS; explicit self-test 192 passed, 2 skipped, 251 subtests passed.
- Clean-tree output and Git-export roots after all smoke steps: absent.
- Database connection attempted: false.
- Prompt 10 rerun gate: **PASS**.
- Next authorized prompt: Prompt 15.

## Prompt 15 — Final fine-comb audit and freeze gate

Prompt 15 independently audited the repository rather than accepting earlier
report claims. The candidate implementation commit is
`d47dd7b2cd53a25db6fccbb119b2fe219e2e8c1d`; Prompt 15's documentation-only
working-tree updates remain uncommitted because no commit, tag, release, or
deployment was authorized.

### Complete scope and structural audit

- All 209 tracked files decoded successfully as UTF-8 text; no tracked binary
  file or parse error was found.
- All 79 Python files parsed through the AST, all 4 JSON files parsed, and the
  tracked TOML configuration parsed. Duplicate decorators: zero.
- Scope includes 52 production Python modules, 26 tests, 8 Web templates,
  5 Web static assets, the Windows launchers, packaging/configuration, the
  Windows/Python 3.11 workflow, 96 prompt/governance files, and all root
  runtime/safety/operator/release documents.
- All four tracked prompt-pack checksum sets passed: 89 entries and zero
  missing or mismatched files.
- Package version `0.3.1` is intentional and identical in
  `pyproject.toml` and `mssql_database_documenter.__version__`. The
  user-facing release name remains `v3.1.1`.
- Git history from required baseline
  `e2188237809efdcc324a79930640628a3975c8d6` contains four intentional
  hardening commits. Candidate HEAD and upstream are synchronized at
  `0 ahead / 0 behind`.

### Named regression search

| Regression class | Independent result |
|---|---|
| Eager output/Git-export roots | PASS — no module-scope evidence write; isolated compile/import/dry-run created neither sentinel root |
| Arbitrary SQL or unguarded cursor | PASS — all 35 registered queries validate; every driver execution site is behind `ReadOnlyCursor` |
| Discovered code, stored program, Agent, or shell execution | PASS — no production `eval`/`exec`/shell/process surface; only the fixed offline developer self-test uses a subprocess |
| Raw samples/profile text in Git export | PASS — raw policy is impossible, default samples are excluded, unknown text is masked/withheld, and staged exports are independently audited |
| Remote/external/opaque view sampling | PASS — all deny branches fail closed in permanent regressions; neither live database contained such a view, so regression evidence is authoritative |
| Misleading report action | PASS — new live discovery and offline selected-run regeneration have distinct CLI/Web actions |
| Safe/full mode aliasing | PASS — resolved policies are materially distinct and bounded by hard ceilings |
| Runtime pytest coupling | PASS — discovery runtime does not import or invoke pytest; self-test is an explicit developer-only action |
| Two-run-only assumptions | PASS — comparison accepts exactly two or three runs and real three-run history/filter/export smoke passed |
| Path containment/reparse regression | PASS — containment suite green; absolute, traversal, symlink, and junction escapes remain denied |
| External dependency queries | PASS — pass-through SQL is rejected and live evidence records zero external queries |
| Missing/red CI | PASS — workflow exists and candidate run is green |
| Duplicate decorators | PASS — zero AST duplicates |
| Stale prompt authority | PASS after Prompt 15 documentation repair — older records are explicitly historical and the completed v3.1.1 pack is non-executable |

### Offline, CI, live, and privacy evidence

- Compile and import sanity: PASS.
- Complete offline suite: 189 passed, 2 skipped, 251 subtests passed in
  9.06 seconds. The skips are the existing Windows symlink-creation privilege
  cases; all available containment/junction tests pass.
- Public self-test: PASS; inner suite 189 passed, 2 skipped, 251 subtests in
  8.27 seconds; connection attempted `false`; output/export created `false`.
- Dry-run: PASS; 35/35 registered queries `SAFE`; connection attempted
  `false`; isolated output and Git-export sentinel roots remained absent.
- The first full-suite harness attempt set global sentinel root overrides that
  intentionally superseded one test fixture's temporary dotenv path. That
  harness-only attempt reported 188 passes and one fixture-path failure. The
  clean-environment rerun above passed completely; no application change was
  required.
- GitHub Actions: workflow `Offline developer quality gate`, Windows/Python
  3.11, run `34119252029`, `completed / success` for candidate HEAD.
- DB1 runs: metadata `20260907_120858` `COMPLETED`; metadata+logic
  `20260907_121315` `COMPLETED`; safe-profile `20260907_121708`
  `COMPLETED_WITH_WARNINGS`, with one contained inaccessible-view warning
  and no failed stage.
- DB2 runs: metadata `20260907_123808` `COMPLETED`; metadata+logic
  `20260907_124007` `COMPLETED`; safe-profile `20260907_124647`
  `COMPLETED_WITH_WARNINGS`, with one contained inaccessible-view warning
  and no failed stage.
- Both independent live evidence audits, all explicit Git-export audits,
  checksum recalculations, offline report regenerations, and both real
  two/three-run comparison smoke cycles passed.
- Baseline-to-working-tree configured server, login, password, and database
  value findings: zero. `.env`, `output/`, and `git_export/` have zero
  tracked files.

### Final acceptance matrix

| Acceptance condition | Result |
|---|---|
| P0 | PASS — 0 open |
| P1 | PASS — 0 open |
| Unresolved P2 | PASS — 0 open |
| Offline suite/self-test/dry-run | PASS |
| GitHub Actions | PASS — run `34119252029` |
| DB1 validation | PASS |
| DB2 validation | PASS |
| Git safety/profile privacy | PASS |
| External/opaque-view rule | PASS |
| Offline report regeneration | PASS |
| Two/three-run comparison | PASS |
| Documentation truthfulness | PASS after stale v3.1 status repair |
| Current prompt authority | PASS — hardening pack marked executed/historical |
| Secret/PII in candidate diff | PASS — none found |

No P0, P1, or unresolved P2 finding remains.

## Final changed-file list

The complete baseline-to-candidate set contains 56 tracked files:

```text
.env.example
HTML_FEATURE_CHECKLIST.md
OPERATOR_RUN_GUIDE.md
Prompts/README.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/00_START_HERE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/01_MASTER_HARDENING_PROMPT.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/02_BASELINE_AND_GUARDRAILS.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/03_FIX_WINDOWS_CI_PATH_CANONICALIZATION.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/04_EXTERNAL_AND_OPAQUE_VIEW_SAMPLING_GATE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/05_GIT_EXPORT_PROFILE_VALUE_PRIVACY.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/06_CLI_REPORT_SEMANTICS.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/07_METADATA_INVENTORY_CONNECTION_FAILURE_LIFECYCLE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/08_CODE_AND_PROMPT_GOVERNANCE_CLEANUP.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/09_TARGETED_REGRESSION_SUITE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/10_READONLY_SECURITY_AND_EVIDENCE_REAUDIT.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/11_FULL_OFFLINE_AND_CI_GATE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/12_LIVE_DB1_READONLY_VALIDATION.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/13_LIVE_DB2_READONLY_VALIDATION.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/14_GIT_EXPORT_REPORT_AND_COMPARISON_SMOKE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/15_FINAL_FINE_COMB_AND_FREEZE_GATE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/ACCEPTANCE_MATRIX.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/DO_NOT_CHANGE_SCOPE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/FINAL_FREEZE_CHECKLIST.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/IMPLEMENTATION_REPORT_TEMPLATE.md
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/PACK_CHECKSUMS.sha256
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/PACK_MANIFEST.json
Prompts/SchoolERP_MSSQL_Documenter_v3_1_1_Hardening_Prompt_Pack/SOURCE_FINDINGS_REFERENCE.md
README.md
V3_1_1_HARDENING_REPORT.md
V3_1_FINAL_FILE_AUDIT.md
V3_1_REMEDIATION_REPORT.md
V3_FILE_AUDIT.md
V3_IMPLEMENTATION_REPORT.md
main.py
src/mssql_database_documenter/cli.py
src/mssql_database_documenter/config.py
src/mssql_database_documenter/evidence_safety.py
src/mssql_database_documenter/git_export.py
src/mssql_database_documenter/inventory.py
src/mssql_database_documenter/lineage/stages.py
src/mssql_database_documenter/profiling/__init__.py
src/mssql_database_documenter/profiling/sampler.py
src/mssql_database_documenter/profiling/stages.py
src/mssql_database_documenter/reporting/stages.py
src/mssql_database_documenter/web/api.py
src/mssql_database_documenter/web/templates/dashboard.html
src/mssql_database_documenter/web/templates/help.html
tests/test_cli_report_semantics.py
tests/test_config.py
tests/test_evidence_safety.py
tests/test_git_export_policy.py
tests/test_inventory.py
tests/test_path_containment.py
tests/test_runtime_self_test.py
tests/test_sampler.py
tests/test_web_app.py
```

The original Prompt 15 cycle changed nine documentation/governance files:
`HTML_FEATURE_CHECKLIST.md`, `OPERATOR_RUN_GUIDE.md`,
`Prompts/README.md`, `README.md`, `V3_1_1_HARDENING_REPORT.md`,
`V3_1_FINAL_FILE_AUDIT.md`, `V3_1_REMEDIATION_REPORT.md`,
`V3_FILE_AUDIT.md`, and `V3_IMPLEMENTATION_REPORT.md`.

## Residual limitations

- The live databases are online and not globally marked read-only. Safety
  therefore continues to depend on least-privilege credentials plus
  `ApplicationIntent=ReadOnly`, fail-closed SQL validation, guarded cursors,
  disabled autocommit, rollback, and operator process controls.
- Each live safe-profile run records one contained inaccessible-view warning.
  No stage failed; unavailable evidence must not be interpreted as absence.
- Neither live database contained an external/opaque view. The mandatory
  regression suite is authoritative for the fail-closed skip branch.
- Full-readonly mode was not separately authorized or rerun during hardening.
  Its offline policy and regression gates pass, but any future live use still
  requires an approved maintenance window.
- Historical runtime evidence predating the final masking repair remains local
  diagnostic evidence and must not be exported or shared.
- Runtime evidence under `output/` and `git_export/` remains ignored and
  uncommitted. Prompt 15 created no tag, release, deployment, or database
  change.

## Original freeze decision — superseded

> **MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE**

Candidate implementation SHA:
`d47dd7b2cd53a25db6fccbb119b2fe219e2e8c1d`.

The declaration above applied to the original candidate and was superseded by
the reopened containment audit.

## Reopened Prompt 15 — final fine-comb status

Local acceptance evidence for the repaired working tree:

- complete offline suite: 192 passed, 2 platform-privilege skips,
  251 subtests passed;
- compile and import: PASS;
- clean-copy self-test: PASS, no database connection and no runtime roots;
- dry-run SQL registry: 35 SAFE, zero unsafe;
- 209 tracked files inventoried; 79 Python files, 26 test files, 8 Web
  templates, 5 static assets, and 96 prompt files;
- all four prompt-pack checksum manifests: 89 entries, zero failures;
- configured server/database/login/password values in the repository diff:
  zero;
- initial inventory and full-run database-parent junction regressions: PASS;
- prior live DB1/DB2, Git-export, regeneration, and comparison evidence remains
  preserved and internally valid.

Candidate CI:

- Commit: `1dc8825c2445342e44ee59ca609770284ffd8d3b`.
- GitHub Actions run: `34141997707`.
- Workflow/job: `Offline developer quality gate` /
  `Windows / Python 3.11 / offline`.
- Result: completed successfully; checkout, dependency installation,
  compile/import, complete offline regression suite, and clean-root assertions
  all passed.

Current decision:

> **MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE**

No tag, release, deployment, or database change is authorized by this status.
