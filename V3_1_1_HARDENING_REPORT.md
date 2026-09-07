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
| 03 | COMPLETE — CI GREEN | `tests/test_runtime_self_test.py`, `tests/test_web_app.py`, report | 2 targeted; 10 related; full suite 159 passed; CI PASS | Windows/Python 3.11 run `34088858063` passed. |
| 04 | COMPLETE | `profiling/sampler.py`, `profiling/__init__.py`, `profiling/stages.py`, `reporting/stages.py`, `tests/test_sampler.py`, report | 23 focused; 58 related; full suite 172 passed, 2 skipped, 247 subtests | Fail-closed local-only view eligibility; exact skip status is indexed and counted in coverage. |
| 05 | COMPLETE | `config.py`, `git_export.py`, `evidence_safety.py`, Web export/help, `.env.example`, README, tests, report | 28 focused; full suite 179 passed, 2 skipped, 247 subtests | Secure staged-copy profile-value policy and independent fail-closed verification. |
| 06 | COMPLETE | `main.py`, `cli.py`, README, operator guide, `tests/test_cli_report_semantics.py`, report | 22 focused/related, 14 subtests; full suite 186 passed, 2 skipped, 249 subtests | Live discovery and offline selected-run regeneration are now unambiguous. |
| 07 | COMPLETE | `inventory.py`, `tests/test_inventory.py`, report | 17 focused/related, 59 subtests; full suite 189 passed, 2 skipped, 249 subtests | Every reserved inventory root is immediately manifested and handled connection failures finalize as sanitized `FAILED` evidence. |
| 08 | COMPLETE | `lineage/stages.py`, `Prompts/README.md`, report | Compile/import PASS; 11 focused tests passed | Duplicate decorator removed with no behavior change; every top-level prompt generation is classified by authority and supersession status. |
| 09 | COMPLETE | `tests/test_sampler.py`, report | 163 passed, 2 skipped, 228 subtests passed | All v3.1.1 findings and protected v3.1 guarantees map to permanent behavioral regressions; encrypted and opaque view cases are now explicit. |
| 10 | COMPLETE | Report only | 110 passed, 2 skipped, 40 subtests; self-test 189 passed, 2 skipped, 251 subtests | Read-only SQL, Web controls, evidence transformations, containment, sanitization, and clean-directory laziness re-audited; no P0/P1 found. |
| 11 | IN PROGRESS — LOCAL PASS / CI PENDING | Report only | Compile/import PASS; 189 passed, 2 skipped, 251 subtests; self-test PASS; dry-run 35 SAFE | Local clean-start gate passed; completion is blocked on an approved commit/push and green Windows/Python 3.11 GitHub Actions run for the current changes. |
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

Prompt 11 local acceptance is complete, but the prompt is not yet PASS because
the current accumulated hardening changes have not received approval to be
committed and pushed for their mandatory GitHub Actions run.

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
- Last committed SHA: `e3041accb980e8db9af39ad968cdac5422328daa`.
- Current Prompt 04–10 hardening changes: not committed or pushed.
- Workflow run ID/URL/conclusion for current changes: pending.
- Gate decision: **LOCAL PASS / CI PENDING — PROMPT 11 INCOMPLETE**.
- Required next action: obtain explicit approval to stage, commit, and push the
  accumulated hardening changes, then monitor Windows/Python 3.11 GitHub
  Actions to a green conclusion.
- Prompt 12 is **not safe to start** until this CI gate passes. Live validation
  remains unauthorized.

## Live validation

Not authorized or started.

## Final changed-file list

Not final. Through the local portion of Prompt 11, hardening has changed
`tests/test_runtime_self_test.py`, `tests/test_web_app.py`,
`src/mssql_database_documenter/profiling/sampler.py`,
`src/mssql_database_documenter/profiling/__init__.py`,
`src/mssql_database_documenter/profiling/stages.py`,
`src/mssql_database_documenter/reporting/stages.py`, `tests/test_sampler.py`, and
`V3_1_1_HARDENING_REPORT.md`. Prompt 05 additionally changes `.env.example`,
`README.md`, `src/mssql_database_documenter/config.py`,
`src/mssql_database_documenter/git_export.py`,
`src/mssql_database_documenter/evidence_safety.py`,
`src/mssql_database_documenter/web/api.py`, the dashboard and Help templates,
`tests/test_config.py`, `tests/test_evidence_safety.py`, and
`tests/test_git_export_policy.py`. Prompt 06 additionally changes `main.py`,
`src/mssql_database_documenter/cli.py`, `OPERATOR_RUN_GUIDE.md`, README command
examples, and adds `tests/test_cli_report_semantics.py`.
Prompt 07 additionally changes `src/mssql_database_documenter/inventory.py` and
`tests/test_inventory.py`. Prompt 08 additionally changes
`src/mssql_database_documenter/lineage/stages.py` and adds `Prompts/README.md`.
Prompt 09 further extends `tests/test_sampler.py` with explicit encrypted and
opaque view regression inputs; it changes no production file. Prompt 10 changes
only this report. Prompt 11's local gate also changes only this report; its
commit/push and CI evidence remain pending.

## Residual limitations

To be completed during sequential hardening.

## Freeze decision

`NOT READY TO FREEZE`
