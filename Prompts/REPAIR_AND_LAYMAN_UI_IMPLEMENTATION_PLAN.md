# MSSQL Documenter Repair and Layman UI Implementation Plan

Date: 2026-08-31  
Scope: v2 discovery engine and v3 Flask Web UI  
Status: In progress

## 1. Objective

Repair the live-run defects found during the end-to-end audit and make the local Web UI understandable to a non-technical operator. The completed system must remain strictly read-only against SQL Server, preserve complete canonical evidence, prevent raw sensitive data from entering a Git export, and explain each action before the operator uses it.

## 2. Confirmed findings to repair

1. `COLUMN_PROFILE.csv` can contain raw minimum and maximum values for columns later classified as PII, credentials, financial, health, or potentially sensitive.
2. The safe-to-commit scan checks configured connection secrets but does not detect unmasked sensitive profile values.
3. Git export allowlists CSV files and could copy unsafe profile evidence.
4. Trusted generated HTML is cleaned with an allowlist that escapes document/report elements, so reports are not presented correctly.
5. Dashboard action cards inherit a horizontal button layout and can overlap their titles and descriptions.
6. The requirements-only installation instructions do not install the `src`-layout package required by the documented legacy module CLI.
7. The UI exposes the required controls but does not explain the workflow, concepts, consequences, evidence types, modes, comparison semantics, or safe Git-export lifecycle at a layman level.

## 3. Non-negotiable safety constraints

- Execute only predefined read-only SQL discovery queries.
- Do not add arbitrary SQL, shell execution, programmable-object execution, database writes, SQL Agent execution, or sequence advancement.
- Classify sensitivity before any value-bearing profiling result is persisted.
- When masking is enabled, raw sensitive values must never reach disk in profiles, distributions, samples, reports, manifests, or exports.
- Credential-like columns are always redacted, regardless of optional settings.
- Git export must independently reject unsafe evidence; it must not trust a previously generated checklist.
- Existing run folders are immutable historical evidence. Corrections apply to new runs; old unsafe runs must not be exported.
- Canonical evidence remains available in raw/download form where it is safe to retain.

## 4. Implementation sequence

### Phase A — Sensitive profile protection

1. Add a reusable sensitivity-classification and masking policy for value-bearing evidence.
2. During column profiling, classify each column before persisting minimum/maximum values.
3. Redact credential extrema and deterministically pseudonymize other sensitive extrema when `PROFILE_MASK_SENSITIVE_DATA=true`.
4. Apply the same policy to low-cardinality distributions so raw sensitive categories cannot be written there.
5. Add explicit masking metadata to profile evidence where practical so operators can distinguish masked values from database values.
6. Preserve non-sensitive aggregate metrics such as counts, percentages, lengths, and numeric statistics when they do not reveal sensitive values.

Acceptance:

- No raw credential, PII, financial, health, or potentially sensitive extrema/distribution value is written when masking is enabled.
- Credential values remain redacted even if general masking is disabled.
- Deterministic masking produces stable comparison-friendly tokens.

### Phase B — Safe-to-commit and Git-export hardening

1. Create a centralized run-evidence safety audit used by both prompt 17 and Git export.
2. Audit value-bearing profile files against sensitivity classifications and allowed masked-token formats.
3. Reject any classified sensitive profile row that contains a non-empty, non-masked raw extrema value.
4. Reject any sensitive low-cardinality distribution containing an unmasked raw value.
5. Continue scanning forbidden files, configured connection secrets, connection strings, secret assignments, caches, temporary files, and unrestricted logs.
6. Make `SAFE_TO_COMMIT_CHECKLIST.md` describe the checks actually executed and fail closed when required classification/masking evidence is absent.
7. Run the same audit immediately before copying a Git export.

Acceptance:

- An intentionally unsafe fixture cannot pass acceptance or Git export.
- A correctly masked run passes and exports only allowlisted sanitized evidence.
- A failed export creates no partial target directory.

### Phase C — Renderer and presentation repair

1. Repair trusted report rendering without allowing script execution, inline event handlers, remote resources, or unsafe URLs.
2. Prefer extracting and sanitizing the report body over rendering an entire HTML document inside the application shell.
3. Preserve safe report structure, tables, headings, sections, and limited presentation classes/styles needed by generated reports.
4. Retain raw view and download links for every formatted preview.
5. Correct action-card layout so title and description always stack and remain readable at desktop and mobile widths.
6. Add print-friendly and accessible focus/keyboard behavior where needed.

Acceptance:

- Generated documentation reports display as formatted content rather than escaped markup.
- Script, iframe, event-handler, and unsafe-link payloads are removed.
- Action-card content does not overlap at supported viewport sizes.

### Phase D — Layman-oriented UI guidance

Add guidance directly where decisions are made, using plain language and progressive disclosure.

1. Global “How this works” section:
   - what the tool reads;
   - what it never changes;
   - the five-step recommended workflow;
   - the difference between output evidence and sanitized Git export.
2. Dashboard action guide:
   - purpose, expected duration/load, output, and safe next step for Dry Run, Test Connection, Metadata, Metadata + Logic, Safe Profile, Full Read-only, Cancel, and Git Export;
   - mode recommendation and warning levels;
   - explanation of configured database selection and settings.
3. Job help:
   - meanings of queued/running/completed/completed-with-warnings/failed/cancelled;
   - progress, logs, warnings, and cancellation behavior.
4. Evidence browser help:
   - folder/run/file hierarchy;
   - Output versus Git Export;
   - formatted preview versus raw/download;
   - search, sort, pagination, and safety limitations.
5. Run-detail help:
   - run identity, stage coverage, warnings/errors, masking status, checklist meaning, and why a completed run may still be unsafe to export.
6. Comparison help:
   - Run A/B/C roles;
   - added/removed/changed/unchanged meanings;
   - mixed-database warnings;
   - FACT/INFERENCE/UNKNOWN and the rule against inferring causality or business equivalence;
   - in-memory comparison versus explicit export.
7. File-view help:
   - what the current renderer shows;
   - how to reach canonical evidence;
   - why large files are paginated;
   - interpretation notes for CSV, JSON, SQL, Markdown, Mermaid, text, and HTML.
8. Add a dedicated Help page linked from persistent navigation with glossary, workflow, safety model, evidence map, troubleshooting, and frequently asked questions.

Acceptance:

- A first-time non-technical operator can identify the correct first action and the next safe action without reading source code or prompt files.
- Every interactive action has an adjacent explanation or contextual help.
- Warnings use plain language and state what the operator should do next.

### Phase E — Packaging and operator documentation

1. Update installation instructions to install the project itself, not only its dependencies.
2. Update the operator guide to match the UI workflow and safety gates.
3. Document that historical runs created before the repair may contain unmasked profile extrema and must not be exported without re-running.
4. Update implementation/checklist documents so they do not claim a pass contradicted by live evidence.

Acceptance:

- A clean virtual environment can run both `main.py` and `python -m mssql_database_documenter` using documented commands.
- Documentation and UI use the same names and workflow order.

### Phase F — Tests and verification

Automated tests:

- profile masking for every sensitivity category;
- credential redaction with general masking disabled;
- sensitive low-cardinality masking;
- unsafe-profile acceptance rejection;
- unsafe Git-export rejection and no partial copy;
- safe export success;
- trusted HTML formatting and malicious HTML removal;
- dashboard/help routes and explanatory copy;
- existing security, comparison, browser, CLI, and discovery regressions.

Live verification:

1. Run the full automated suite.
2. Run offline dry-run and both configured connection tests.
3. Run a new sequential `full-readonly` discovery for each configured database.
4. Independently join sensitivity classifications to profile/distribution evidence and confirm zero raw sensitive values.
5. Validate required outputs, manifests, checksums, coverage, warnings, and errors.
6. Create a Git export only after the new run passes the hardened audit.
7. Inspect dashboard, Help, browser, run detail, file renderers, comparisons, responsive layout, and error states in a real browser.
8. Confirm loopback binding, CSP, Host validation, traversal blocking, CSRF, and no browser console errors.

## 5. Completion criteria

The repair is complete only when:

- every automated test passes apart from explicitly documented environment-only skips;
- new live runs complete sequentially without unresolved errors;
- sensitive profile audit reports zero raw leaks;
- safe Git export succeeds only for the repaired runs;
- generated HTML renders correctly and safely;
- UI controls and help text are readable and understandable at desktop and mobile widths;
- documentation matches actual commands and behavior;
- the final implementation report lists evidence, remaining limitations, and any skipped verification.

## 6. Recovery and rollback

- Source changes are small, isolated, and covered by regression tests.
- No existing output or Git-export run is overwritten or deleted.
- Failed new discovery/export directories remain identifiable by status and are not treated as safe handoff evidence.
- If a phase fails, later phases that depend on it do not proceed until it is corrected and re-tested.

## 7. Progress log

- [x] End-to-end audit completed and defects confirmed.
- [x] Repair plan documented before source changes.
- [x] Phase A — Sensitive profile protection.
- [x] Phase B — Safe-to-commit and export hardening.
- [x] Phase C — Renderer and presentation repair.
- [x] Phase D — Layman-oriented UI guidance.
- [x] Phase E — Packaging and operator documentation.
- [x] Phase F — Automated and live verification.

Final evidence:

- 86 automated tests passed; 2 Windows symlink-privilege tests skipped.
- Both configured databases passed offline, connection, and sequential full-read-only validation.
- Fresh run masking audits passed with zero violations across 11,933 checked sensitive values.
- Fresh run manifests matched actual file counts and every SHA-256 checksum matched.
- Explicit Git exports passed the same independent audit and contained no partial copies.
- Desktop and 390-pixel browser verification passed with no document-width overflow.
