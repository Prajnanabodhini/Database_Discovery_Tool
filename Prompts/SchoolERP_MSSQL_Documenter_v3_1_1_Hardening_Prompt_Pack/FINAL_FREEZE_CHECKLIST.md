# v3.1.1 Final Freeze Checklist

## Repository

- [ ] Candidate based on approved HEAD
- [ ] No unrelated changes
- [ ] Version identity intentional
- [ ] Prompt authority updated
- [ ] Historical evidence preserved

## Database safety

- [ ] Read-only connection unchanged/stronger
- [ ] Autocommit false
- [ ] Rollback/close
- [ ] SQL validator PASS
- [ ] Cursor proxy PASS
- [ ] No DML/DDL/admin SQL
- [ ] No SP execution
- [ ] No Agent execution
- [ ] No discovered-code execution
- [ ] External/opaque views not sampled

## Privacy

- [ ] Credentials absent
- [ ] Server/login sanitized
- [ ] Raw sample Git policy impossible
- [ ] Default sample payload policy exclude
- [ ] Unknown text profile values protected in Git export
- [ ] Source run not mutated
- [ ] staged export independently audited
- [ ] checksums valid

## Runtime/Web

- [ ] no eager output root
- [ ] no eager Git-export root
- [ ] loopback
- [ ] CSRF
- [ ] same-origin
- [ ] path containment
- [ ] no arbitrary SQL/shell
- [ ] report regeneration offline

## Tests

- [ ] compile PASS
- [ ] import PASS
- [ ] complete offline pytest PASS
- [ ] self-test PASS
- [ ] dry-run PASS
- [ ] no runtime roots from offline gate
- [ ] GitHub Actions GREEN

## Live

- [ ] DB1 metadata PASS
- [ ] DB1 metadata+logic PASS
- [ ] DB1 safe-profile PASS
- [ ] DB1 evidence audit PASS
- [ ] DB2 PASS if authorized/configured
- [ ] Git export PASS
- [ ] offline regeneration PASS
- [ ] 2-run comparison PASS
- [ ] 3-run comparison PASS

## Documentation

- [ ] README truthful
- [ ] operator guide truthful
- [ ] safety model truthful
- [ ] hardening report complete
- [ ] no old v3.1 readiness claim presented as current authority
- [ ] residual limitations explicit

## Decision

Only when every mandatory item above is satisfied:

`MSSQL DOCUMENTATION TOOL v3.1.1 — READY TO FREEZE`
