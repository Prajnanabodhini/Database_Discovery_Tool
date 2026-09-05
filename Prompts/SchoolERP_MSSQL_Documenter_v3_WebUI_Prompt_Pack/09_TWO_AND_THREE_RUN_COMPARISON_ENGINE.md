# Prompt — 2-Run and 3-Run Comparison Engine

Implement comparison for 2 or 3 selected runs.

Inputs:
Run A
Run B
optional Run C

Comparison categories:
- summary metrics
- schemas
- tables
- columns
- types
- PK/FK
- inferred relationships
- indexes
- constraints
- views
- procedures
- functions
- triggers
- synonyms
- sequences
- row counts
- sizes
- shapes
- definition hashes
- dependencies
- lineage
- pipelines
- data quality
- risks
- coverage/errors

Use stable normalized keys.

Statuses:
UNCHANGED
ADDED
REMOVED
CHANGED
NOT_AVAILABLE
NOT_COMPARABLE

For 3 runs calculate:
A→B
B→C
A→C

Detect:
ADDED_IN_B
ADDED_IN_C
REMOVED_IN_B
REMOVED_IN_C
CHANGED_A_TO_B
CHANGED_B_TO_C
CHANGED_BOTH
REVERTED_TO_A

Never infer cause.
