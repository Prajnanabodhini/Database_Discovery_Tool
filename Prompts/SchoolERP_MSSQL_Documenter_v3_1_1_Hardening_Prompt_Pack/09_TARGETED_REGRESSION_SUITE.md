# Prompt 09 — Build the v3.1.1 Targeted Regression Suite

## Objective

Ensure every v3.1.1 finding has a permanent automated regression.

## Required test families

### Windows path identity

- self-test cwd identity
- report regeneration output containment
- short/long path aliases
- existing reparse/junction tests

### external view safety

- local view allowed
- cross-database view denied
- linked-server view denied
- external constructs denied
- opaque/encrypted/unresolved view denied
- table sampling unaffected

### Git profile-value privacy

- unknown text extrema
- unknown low-cardinality text
- known PII
- credential
- Non-sensitive explicit allow
- aggregate-only
- manifest/checksum accuracy
- no source mutation

### CLI report semantics

- help
- all/discover
- offline regeneration
- no connection during regeneration

### inventory failure

- initial connection failure
- truthful status/cleanup
- no orphan path

### regression of v3.1 guarantees

Do not remove existing tests for:
- SQL validator
- cursor proxy
- Agent no-execution
- mode distinctions
- sensitivity reconciliation
- Git sample exclusion
- comparison 3-run timeline
- Web CSRF/loopback
- path containment
- lazy roots
- runtime pytest decoupling
- metadata completeness

## Test-quality rules

- avoid platform-specific literal paths;
- do not assert only implementation details when behavior can be asserted;
- mocks must fail if a prohibited DB connection or subprocess occurs;
- do not weaken a test merely to make CI green.

## Output

Append a regression matrix to `V3_1_1_HARDENING_REPORT.md` with:

Finding → test file → test name(s) → result.
