# Prompt 03 — PII and Git Export Hardening

## Objective
Make sample privacy fail-safe for legacy School ERP schemas and public Git handoff.

## Required design
- Extract sensitivity logic from `fullrun.py`.
- Classification returns category/action/confidence/evidence.
- Layer overrides → built-in legacy/modern heuristics → extended properties → obvious safe value-pattern signals.
- Add `config/sensitivity_overrides.toml.example` with documented precedence.
- Recognize legacy examples: StudNm, FName, MName, MobNo, PhNo, ContactNo, Addr1, ResAdd, BDate, BirthDt.

## Git sample policy
Add `GIT_EXPORT_SAMPLE_POLICY=exclude|masked_only`; default `exclude`; no raw mode.
- `exclude`: omit sample payload CSVs but keep index/masking/sensitivity evidence.
- `masked_only`: create a sanitized export copy; do not mutate the original run.
- Export manifest/checklist records policy.
- Export-time audit remains independent/fail-closed.

## Tests
Use synthetic legacy PII. Prove override precedence, raw sensitive fixture rejection, default sample exclusion, masked-only no leakage, original output unchanged, no DB needed.

STOP.
