# Runtime Output Contract

This document describes outputs, but they must not be created during project scaffolding.

At actual run time:

```text
output/
└── <database>/
    └── run_<timestamp>/
        ├── 00_Run_Metadata/
        ├── 01_Executive_Summary/
        ├── 02_Server_Database/
        ├── 03_Schemas/
        ├── 04_Tables/
        ├── 05_Columns/
        ├── 06_Keys_Relationships/
        ├── 07_Indexes_Constraints/
        ├── 08_Views/
        ├── 09_Stored_Procedures/
        ├── 10_Functions/
        ├── 11_Triggers/
        ├── 12_Synonyms_Sequences/
        ├── 13_Data_Profiling/
        ├── 14_Samples/
        ├── 15_Lineage/
        ├── 16_Pipelines/
        ├── 17_Data_Quality/
        ├── 18_Risks_Uncertainties/
        ├── 19_Diagrams/
        ├── 20_Object_Documentation/
        ├── 21_HTML_Report/
        └── 99_Git_Handoff/
```

Git Export is created only on explicit action:

```text
git_export/
└── MSSQL/
    └── <database>/
        └── <run_id>/
```

The export must contain sanitized evidence and presentation files only.

Never include `.env`, credentials, secrets, raw unmasked sensitive data, caches, temp files or unrestricted internal logs.
