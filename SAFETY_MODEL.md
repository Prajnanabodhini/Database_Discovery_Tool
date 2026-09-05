# Safety Model

## Invariants

1. Only explicitly registered, project-owned, read-only SQL is eligible for execution.
2. Every statement is validated immediately before execution, not only at registration time.
3. Accepted statements must be a single `SELECT` or `WITH ... SELECT` query.
4. DML, DDL, administrative commands, procedure/function/job execution, `SELECT INTO`, sequence advancement, transaction control, and external pass-through queries are rejected.
5. Database names come only from explicit configuration or `--database`; the application never scans all server databases.
6. Stored procedures, functions, triggers, and jobs are never executed for discovery. Later stages may inspect their catalog metadata and definitions only.
7. Credentials remain in process environment or a local ignored `.env`. Diagnostics use a redacted configuration view.
8. Timeouts and profiling thresholds are mandatory for live work. Read-only does not imply low resource usage.

## Fail-closed behavior

An unknown, empty, multi-statement, unparsable, or suspicious query is denied. Comments and string literals are removed before token checks so forbidden operations cannot be hidden in comments and harmless words inside string literals do not cause false permission. A rejected query raises `UnsafeSqlError` before any cursor receives it.

## Layered controls

- Use a dedicated SQL login or Windows identity with only the required reader permissions.
- Run `dry-run` and offline tests before `test-connection`.
- Start live discovery in metadata mode.
- Keep masking enabled before any sample-data stage.
- Stop immediately if generated SQL is unexpected or write-capable.

## Web control plane

- The Flask server binds only to an explicit loopback host; non-loopback configuration is rejected.
- State-changing requests require a session CSRF token and same-origin browser context.
- The API exposes a fixed action allowlist. It has no arbitrary SQL, Python, process, or shell endpoint.
- Only one controlled job may run at a time. Cancellation is observed at stage boundaries so partial evidence can be finalized with a `CANCELLED` status.
- Output and Git-export paths are resolved beneath configured roots. Absolute paths, traversal, and symlink escapes are rejected.
- Logs and configuration responses are redacted. Generated samples use the v2 masking rules.
- Comparison is read-only. Files are created only for an explicit export request.
- Git handoff is never automatic; an explicit action scans a manifested output run for forbidden files and configured sensitive values before copying.

## Known boundary

The application guard controls only SQL issued by this application. It cannot repair an over-privileged database login, prevent another program from using those credentials, or guarantee that a large read query has negligible production impact.
