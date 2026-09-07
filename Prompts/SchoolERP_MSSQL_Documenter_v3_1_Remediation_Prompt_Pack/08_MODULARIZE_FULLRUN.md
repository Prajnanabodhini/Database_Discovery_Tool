# Prompt 08 — Modularize `fullrun.py`

## Objective
Turn the monolith into a maintainable modular engine without evidence-semantic regression.

Refactor incrementally with characterization tests before extraction.

Target ownership:
- profiling: sensitivity, sampling, column/table policy
- relationships: inference, cardinality, validation/orphans
- lineage: static SQL, dependencies, Agent, pipeline
- analysis: classification, duplicates, quality, risk
- reporting: object docs, diagrams, narratives, HTML, manifests/control files

`fullrun.py` should mainly own run state, stages, cancellation/errors, connection lifecycle and orchestration. Avoid circular imports. Preserve public APIs with compatibility wrappers if needed.

Acceptance: full suite green, no unintended output-contract change, read-only guards unchanged, meaningful reduction of domain logic in `fullrun.py`, file audit documents ownership.

STOP.
