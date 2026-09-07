# Prompt 05 — Harden Git Export for Unknown Data-Bearing Profile Values

## Problem

v3.1 strongly protects sample payload CSVs, but Git export also includes profiling artifacts containing data-bearing fields such as:

- `COLUMN_PROFILE.csv`
  - `minimum_value`
  - `maximum_value`
- `LOW_CARDINALITY_VALUES.csv`
  - `value`

Current classifiers identify many sensitive values, but no heuristic can prove every arbitrary string is non-sensitive.

Example:

```text
column = Value1
value = Alice Example
```

may remain `Unknown / PRESERVE`.

For a generic database documentation tool, Git export must fail safe even when semantic classification is incomplete.

## Objective

Separate **local evidence usefulness** from **Git-publication privacy**.

Local output may retain policy-approved profile values.

Git export must use a stricter policy.

## Required policy

Introduce a configurable Git-export profile-value policy with a secure default.

Recommended contract:

`GIT_EXPORT_PROFILE_VALUE_POLICY=mask_unknown_text`

Allowed v3.1.1 values:

- `mask_unknown_text`
- `aggregate_only`

Do not add `raw`.

### `mask_unknown_text`

During staged Git export only:

- known sensitive values → existing redaction/masking rules;
- `Unknown` string-like profile values → pseudonymize;
- binary values → redact;
- explicitly reviewed `Non-sensitive` may be preserved;
- numeric/date structural metrics may remain if not sensitive by classification;
- never mutate source run evidence.

### `aggregate_only`

For Git staged copy:
- blank/remove value-bearing profile fields;
- retain counts, null rates, distinct counts, status, type and aggregate metrics;
- retain an explicit export-policy marker explaining that raw extrema/distribution labels were withheld.

## Low-cardinality handling

Treat low-cardinality textual values conservatively.

Unknown text values must not be copied raw under the default policy.

## Required artifacts

Extend the Git-export policy record to include:

- `profile_value_policy`
- number of profile values masked
- number omitted
- source evidence mutated = false

Refresh manifest/checksums after staging.

## Evidence audit

The independent Git safety audit must verify the staged result and fail closed.

Do not rely solely on the exporter saying it masked the data.

## Tests

Add tests for:

1. unknown name-like text in min/max → not raw in Git export;
2. unknown address-like text → not raw;
3. known PII → masked;
4. credential → redacted;
5. explicitly Non-sensitive reviewed label → preserved in `mask_unknown_text`;
6. numeric structural extrema handled according to policy;
7. `aggregate_only` removes value payloads;
8. source evidence hash unchanged;
9. staged manifest policy accurate;
10. checksums valid;
11. raw profile policy rejected;
12. default policy secure when no environment override exists.

## Documentation

Clearly distinguish:
- local output;
- Git-safe export.

Never describe Git safety as equivalent to semantic de-identification of all local evidence.
