# Human Pre-Run Safety Review

- [ ] no DML/DDL/admin/EXEC/job/sequence-next operations
- [ ] .env gitignored and secrets redacted
- [ ] dry-run and SQL safety tests pass
- [ ] sample masking enabled and credentials always redacted
- [ ] query timeout and large-table thresholds configured
- [ ] first live run uses metadata or metadata+logic
- [ ] output local only and application files untouched

Recommended sequence: dry-run → test-connection → metadata → review → metadata+logic → review → safe-profile → review → report. Stop if any unexpected write-capable SQL appears.
