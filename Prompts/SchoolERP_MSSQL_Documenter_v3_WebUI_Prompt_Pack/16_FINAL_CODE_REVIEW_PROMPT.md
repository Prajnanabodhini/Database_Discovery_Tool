# Prompt — Fine-Comb Final Code Review

Audit every generated project file.

Produce a table:

```text
File | Purpose | Entry/Callers | Reads | Writes(Local) | DB Access | Web Exposure | Issues | Status
```

Review:
- main.py
- BAT files
- config
- DB connection
- SQL safety
- each metadata module
- each profiling module
- relationship/lineage modules
- reporting
- Git export
- comparison
- web routes/APIs
- job manager
- templates
- JS
- CSS
- tests

Search specifically for:
- eager `mkdir`
- placeholder output generation
- subprocess/shell use
- eval/exec
- arbitrary command endpoints
- arbitrary SQL endpoints
- unsafe path joins
- secrets
- `0.0.0.0`
- concurrency problems
- unbounded reads
- omitted masking
- truncation of evidence
- 2-run-only assumptions
- hardcoded database names

Run tests.

Return PASS/FAIL and exact file/line findings.
