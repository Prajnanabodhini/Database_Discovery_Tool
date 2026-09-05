# Prompt — Read-Only and Production Safety

Retain strict database safety.

Forbidden:
INSERT UPDATE DELETE MERGE TRUNCATE
CREATE ALTER DROP
GRANT REVOKE DENY
BACKUP RESTORE
EXEC EXECUTE
mutating DBCC
job execution
sequence NEXT VALUE
configuration changes

Inspect DB code statically.

All project-owned SQL passes a fail-closed guard.

Profiling must respect:
- timeout
- large-table threshold
- no expensive random sort
- reduced profiling
- exact row-count safety threshold

Web execution does not weaken these rules.
