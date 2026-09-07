# Prompt 14 — Git Export, Offline Report and 2/3-Run Comparison Smoke

## Preconditions

DB1 and DB2 live-read-only validation passed.

## A. Git export

For an approved run:

- create default Git export;
- verify sample policy = exclude;
- verify new profile-value policy;
- verify independent audit PASS;
- verify manifest;
- independently recalculate checksums;
- verify source run hashes unchanged.

Do not commit runtime evidence to the application repository unless the operator explicitly wants a separate/private evidence repository.

## B. Offline report regeneration

Select one manifested run.

Verify:
- no DB connection;
- separate versioned destination;
- source hashes unchanged;
- Markdown/HTML outputs render;
- generated HTML remains sanitized/static where required.

## C. Two-run comparison

Compare two real compatible runs.

Verify:
- added/removed/changed/unchanged;
- numeric deltas;
- definition diffs;
- summary arithmetic;
- explicit export.

## D. Three-run comparison

Use three real runs if available.

Verify:
- A→B
- B→C
- A→C
- added-in-B/C
- removed-in-B/C
- changed A→B
- changed B→C
- reverted-to-A
- changed-both
- filters evaluate full event history
- global summary counts all displayed/exported category rows
- static exported HTML contains evidence with scripts disabled/absent

## Evidence

No PII/raw samples in screenshots or report excerpts.
