# v3.1 Acceptance Matrix

| ID | Requirement | Freeze gate |
|---|---|---|
| A01 | Root `main.py` remains canonical | Yes |
| A02 | Import/start/help/self-test/dry-run are evidence-lazy | Yes |
| A03 | DB SQL remains SELECT-only and read-only intent retained | Yes |
| A04 | No arbitrary SQL/shell Web action | Yes |
| A05 | Legacy sensitive names handled/overrideable | Yes |
| A06 | Git export defaults to excluding sample payloads | Yes |
| A07 | Masked-only export cannot leak raw PII | Yes |
| A08 | Views have controlled sample attempt/status | Yes |
| A09 | Large tables sample independently of profiling | Yes |
| A10 | `safe-profile` materially differs from `full-readonly` | Yes |
| A11 | SQL Agent commands never execute | Yes |
| A12 | Agent static refs/pipeline edges available | Yes |
| A13 | Expanded MSSQL metadata families implemented | Yes |
| A14 | Capability/output/comparison contracts updated | Yes |
| A15 | `fullrun.py` primarily orchestrates | Yes |
| A16 | Production discovery does not run pytest | Yes |
| A17 | `main.py self-test` is offline/lazy | Yes |
| A18 | Comparison HTML works with scripts removed | Yes |
| A19 | 3-run multi-event filters correct | Yes |
| A20 | Comparison summary scope truthful | Yes |
| A21 | Reports action semantics corrected | Yes |
| A22 | Offline CI workflow exists | Yes |
| A23 | Path/symlink containment retained | Yes |
| A24 | Evidence audit remains fail-closed | Yes |
| A25 | Historical runtime evidence untouched | Yes |
| A26 | Docs/help/config updated | Yes |
| A27 | Offline suite passes | Yes |
| A28 | Live DB1 validation | If authorized |
| A29 | Live DB2 validation | If authorized |
| A30 | 3-run live smoke | If compatible runs exist |
| A31 | Final fine-comb audit produced | Yes |

P0 failure = STOP. P1 failure = NOT READY. P2 must be resolved or explicitly accepted/documented.
