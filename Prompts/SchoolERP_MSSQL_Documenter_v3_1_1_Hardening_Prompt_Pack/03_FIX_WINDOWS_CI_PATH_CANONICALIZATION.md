# Prompt 03 — Fix Windows CI Path Canonicalization

## Problem

The v3.1 GitHub Actions workflow is red.

The observed offline suite result is:

- 159 passed
- 2 failed
- 241 subtests passed

Both failures are Windows short-path (`RUNNER~1`) vs long-path (`runneradmin`) representation mismatches.

Affected areas observed in v3.1:

- `tests/test_runtime_self_test.py`
- `tests/test_web_app.py`

## Objective

Make the tests compare filesystem identity/canonical paths correctly without weakening production path containment.

## Required implementation rules

1. Prefer fixing **test assertions** if production behavior is already correct.
2. Do not weaken:
   - `Path.resolve()`
   - `relative_to()` containment
   - symlink/reparse protections
   - output root containment
3. Canonicalize both sides before equality/containment assertions.
4. Use one of:
   - `Path.resolve()` on both values;
   - `os.path.samefile()` where both paths exist;
   - a test helper that resolves both operands.
5. Do not special-case GitHub runner usernames.
6. Do not hardcode `RUNNER~1`, `runneradmin`, drive letters, or temp directories.
7. Keep tests portable to normal Windows 10/11 local development.

## Required tests

Run at minimum:

- the two previously failing tests;
- all path-containment tests;
- all self-test tests;
- all report-regeneration tests;
- complete offline suite.

Expected:

`0 failed`

## CI requirement

A local pass is not sufficient for final acceptance.

After an approved commit/push, GitHub Actions must complete green on Windows/Python 3.11.

## Evidence

Record:
- exact test changes;
- why production code was or was not changed;
- local results;
- later CI run URL/ID and result.

## Stop

Do not proceed to live DB work.
