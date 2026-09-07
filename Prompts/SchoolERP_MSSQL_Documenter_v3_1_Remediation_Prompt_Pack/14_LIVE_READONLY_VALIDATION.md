# Prompt 14 — Live Read-Only Validation

## AUTHORIZATION GATE
Do not execute unless operator/user explicitly authorizes live DB access. `.env` existence is not authorization.

## DB1 only
Dry-run → connection test → metadata → inspect → metadata+logic → inspect → safe-profile → inspect view samples, large-table sample status, sensitivity, Agent refs, new metadata, masking. Full-readonly only if separately approved.

Do not Git-export until safety audit passes. For production, default Git sample policy must be `exclude`; confirm no sample payload CSVs in export and no configured server/user/password strings.

## DB2
Only after DB1 passes; repeat sequentially.

## Comparison
If 3 compatible manifested runs exist, test A/B/C, multi-event filters, static HTML export and opening through the local browser without scripts.

Record exact run IDs/status. Never claim checks not performed.
