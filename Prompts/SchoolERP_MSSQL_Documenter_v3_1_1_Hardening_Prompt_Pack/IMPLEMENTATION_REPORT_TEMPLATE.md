# V3_1_1_HARDENING_REPORT Template

## Header

- Repository:
- Starting SHA:
- Candidate branch:
- Candidate SHA:
- Date:
- Python:
- Operator:
- Initial working tree:
- Initial CI:

## Final verdict

`NOT READY TO FREEZE` until Prompt 15 passes.

## Prompt execution ledger

| Prompt | Status | Files changed | Tests | Notes |
|---|---|---|---|---|

## Finding H-01 — Windows CI

### Root cause

### Code/test change

### Tests

### CI

---

## Finding H-02 — External/opaque view sampling

### Threat model

### Eligibility contract

### Evidence sources

### Skip statuses

### Tests

### Live validation

---

## Finding H-03 — Git profile-value privacy

### Local evidence policy

### Git staged policy

### Tests

### Safety audit

---

## Finding H-04 — CLI report semantics

### Before

### After

### Tests

---

## Finding H-05 — Inventory connection failure

### Before

### After

### Tests

---

## Cleanup

- duplicate decorator:
- prompt authority:

## Security re-audit

## Offline regression results

## GitHub Actions

## DB1 live validation

## DB2 live validation

## Git-export validation

## Report regeneration validation

## Comparison validation

## Final changed-file list

## Residual limitations

## Final priority register

| Severity | Count | Items |
|---|---:|---|

## Freeze decision

Only write `READY TO FREEZE` if all mandatory gates have passed.
