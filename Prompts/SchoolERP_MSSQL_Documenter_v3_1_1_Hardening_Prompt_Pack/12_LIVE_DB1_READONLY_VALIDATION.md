# Prompt 12 — Authorized Live DB1 Read-Only Validation

## Preconditions

Do not run unless:

- Prompt 11 is fully PASS including green GitHub Actions;
- user/operator authorizes live read-only validation;
- configured connection uses intended read-only account/policy;
- first database is explicitly selected.

Do not process a second DB in this prompt.

## Required order

1. dry-run
2. test-connection
3. metadata
4. review metadata evidence
5. metadata+logic
6. review
7. safe-profile
8. review
9. evidence safety audit
10. explicit Git-export staging/audit only if all prior gates pass

## Special v3.1.1 validation

### External view gate

Identify at least:
- one local-only sample-eligible view if available;
- one cross-database/external/opaque view if such a view exists.

Verify:
- local-only view may sample;
- external/opaque view records the explicit skip status;
- no external system is contacted by the tool.

If DB1 has no such external view, record:
`NOT PRESENT IN DB1 — regression test is authoritative`.

### Profile Git privacy

Inspect staged Git export policy:
- no raw sample payload CSV under default policy;
- unknown text profile-value policy present;
- no configured secret/server/login strings;
- checksums valid.

## Do not

- run full-readonly unless separately authorized;
- execute SPs/jobs;
- query an external system to "prove" it was skipped;
- alter the DB.

## Evidence

Record actual run IDs and statuses in the hardening report without copying PII.
