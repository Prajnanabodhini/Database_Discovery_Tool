# Prompt — Tests and Acceptance

Automate tests for:

## Entry point
- main.py exists
- help works
- default routes to web
- CLI routing works

## Lazy lifecycle
- no output on import
- no output on web startup
- no output on dry-run
- test-connection does not create run
- real run creates run path
- git export lazy

## Web
- localhost default
- CSRF
- same-origin
- action whitelist
- no shell
- DB allowlist
- path traversal
- symlink escape

## Browser/renderers
- absent roots
- Markdown
- CSV pagination
- JSON
- text
- SQL
- raw content
- large files

## Jobs
- one-job lock
- statuses
- error capture
- cancellation
- sequential DB processing

## Compare
- 2 runs
- 3 runs
- added/removed/changed
- numeric deltas
- definition diffs
- missing files
- cross-DB warning
- run modes differ
- comparison export

## DB safety
retain all read-only tests.

Do not approve until all critical tests pass.
