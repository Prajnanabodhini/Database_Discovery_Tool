# Prompt 10 — Comparison Semantics and Export Presentation

## Objective
Correct 3-run timeline behavior and make exported HTML useful inside the safe browser.

### Static HTML
Replace JS-dependent export with server-rendered static HTML. Include run metadata, warnings, summary, category sections, A/B/C, A→B/B→C/A→C, timeline events, numeric deltas and definition diffs. No script required. Safe renderer must retain useful visible content.

### Timeline filters
Filter by `timeline_events` and interval statuses, not only one priority status. absent→added→changed must match Added and Changed. Reverted and remove/re-add histories must remain visible.

### Summary totals
Make global/per-category scope explicit and mathematically consistent with displayed rows.

### Exports
JSON/CSV remain canonical machine outputs; HTML is human-readable.

Tests: no script dependency; safe renderer shows content; multi-event filters; summary totals.

STOP.
