# Prompt 05 — Discovery Mode Semantics

## Objective
Make the four modes truthful and materially distinct.

Implement a resolved mode policy dataclass/object instead of scattered booleans.

- metadata: structural catalog only.
- metadata+logic: metadata + programmable definitions/static dependencies/pipeline metadata.
- safe-profile: conservative bounded samples/profiles/sensitivity/relationship validation.
- full-readonly: safe-profile + explicitly deeper read-only checks with larger configurable limits and hard ceilings.

Suggested policy fields: programmable logic, samples, profile threshold, exact counts/ceiling, relationship validation threshold, low-cardinality limit, extended full validation.

Persist resolved policy in run config, summary and manifest. Update UI/help/operator guide.

Tests must prove safe-profile != full-readonly and metadata modes avoid data scans.

STOP.
