# Prompt — Comparison HTML UI

Create a comparison screen with up to three run selectors.

Display run metadata cards.

Allow filters:
- changed only
- added
- removed
- unchanged
- object type
- schema
- severity
- database
- warnings/errors

Three-run table:

```text
Object | Run A | Run B | Run C | A→B | B→C | A→C
```

Numeric metrics display value and delta.

Definition changes offer:
- A vs B diff
- B vs C diff
- A vs C diff

Allow export of comparison to:
- HTML
- CSV
- JSON

Keep raw source links.
