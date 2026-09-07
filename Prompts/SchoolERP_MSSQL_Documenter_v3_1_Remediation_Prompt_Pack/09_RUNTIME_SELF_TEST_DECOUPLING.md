# Prompt 09 — Decouple Developer Tests from Live Discovery

## Objective
A database evidence run must never invoke pytest.

1. Remove pytest subprocess from runtime stage 21.
2. Keep lightweight current-run semantic invariants.
3. Add `python main.py self-test`.
4. Optional Web self-test must be offline, lazy, single-job controlled and sanitized.
5. Fixed argv only; no shell.
6. Discovery must work when pytest/test source is unavailable.

Tests: patch subprocess and prove live-run path never runs pytest; self-test may run pytest; self-test does not connect or create output/export; docs explain distinction.

STOP.
