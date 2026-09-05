# Required HTML Feature Checklist

Verified against the Flask routes, templates, static client code, renderer tests, and
Web integration tests. Canonical files remain available through raw view/download;
formatted presentation never replaces source evidence.

## Dashboard

- [x] Connection/config summary — sanitized `Settings.sanitized()` values only.
- [x] Safety state — fail-closed SQL, loopback, CSRF, masking, and one-job controls.
- [x] Execution buttons — predefined actions only.
- [x] Active job/progress/logs — ID, DB, mode, stage, progress, time, warnings/errors, redacted log.
- [x] Output root link — persistent navigation and recent-run links.
- [x] Git-export root link — persistent navigation and explicit export control.
- [x] Recent runs — manifested output/Git registry.
- [x] Compare link — persistent navigation.
- [x] Recommended first-time workflow — ordered, plain-language steps and resource warning.
- [x] Per-action guidance — purpose, impact, output, and safe next step.
- [x] Job-status help — queued/running/completed/warning/failed/cancelled meanings.
- [x] Dedicated Help link — purpose, workflow, evidence, safety, comparison, troubleshooting, and glossary.

## File browser

- [x] Output/Git Export root selector.
- [x] Breadcrumb navigation.
- [x] Name search and extension filter.
- [x] File size, UTC modified date, and type.
- [x] Formatted safe preview.
- [x] Raw source view.
- [x] Full-data access through streaming pagination and raw/download.
- [x] Download and SQL copy where appropriate.
- [x] Absolute, traversal, resolved containment, and symlink escape protection.
- [x] Plain-language root/folder/file navigation guidance.

## Rendering

- [x] Sanitized Markdown with tables, fenced code, and admonitions.
- [x] CSV columns/search/sort/pagination; large files stream in source order.
- [x] Complete formatted JSON; oversized JSON becomes complete paginated source.
- [x] Paginated text/log/checksum source.
- [x] Paginated SQL definition plus full raw copy/download.
- [x] Paginated Mermaid source.
- [x] Sanitized generated-HTML body rendering with executable markup removed.
- [x] Unsupported file name/size/type metadata plus raw/download fallback.
- [x] File-type-specific help and canonical-source explanation.

## Execution

- [x] Dry run without connection or output.
- [x] Test connection without run creation.
- [x] Metadata.
- [x] Metadata + Logic.
- [x] Safe Profile.
- [x] Full Read-Only confirmation.
- [x] Generate Reports action.
- [x] Explicit Git export.
- [x] Status/progress/logs and safe cancellation.
- [x] No arbitrary command, shell, Python, or SQL endpoint.

## Compare

- [x] Select exactly two runs.
- [x] Select optional third run when enabled.
- [x] Run A/B/C metadata cards and raw/category source links.
- [x] Changed-only, added, removed, unchanged, unavailable, and exact-status filters.
- [x] Numeric values, absolute deltas, and percentage deltas.
- [x] Full A/B/C definitions and unified interval diffs.
- [x] Schema, table, column, constraint/index, and programmable-object categories.
- [x] Dependency, lineage, pipeline, risk/error, quality, and coverage categories.
- [x] Explicit HTML/CSV/JSON comparison export.

Overall result: **PASS**.

Reverified on 2026-08-31 through automated renderer/Web tests and interactive desktop
and 390-pixel responsive browser checks. The mobile document width equals the viewport;
execution-card content stacks without overlap.
