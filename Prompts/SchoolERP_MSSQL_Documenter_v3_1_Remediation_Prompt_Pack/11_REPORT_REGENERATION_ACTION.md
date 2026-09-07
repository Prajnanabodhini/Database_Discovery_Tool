# Prompt 11 — Report Regeneration / Web Action Semantics

## Objective
Remove misleading behavior where "reports" starts a fresh DB discovery.

Preferred: add `regenerate-reports` for one manifested output run. It reads existing canonical artifacts, regenerates presentation outputs, never connects to MSSQL, never mutates canonical raw evidence, and writes safely/versioned.

If full artifact-only regeneration is impractical, remove/rename the misleading action and state that discovery produces reports. Do not claim local regeneration if it touches the DB.

If implemented, test with DB `connect()` patched to fail; regeneration must still succeed and source evidence remain unchanged. Update UI/help/API allowlist.

STOP.
