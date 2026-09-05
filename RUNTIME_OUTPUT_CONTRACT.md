# Runtime Output and Git Export Contract

No source import, installation, dashboard startup, dry run, or connection check creates
runtime roots. A real discovery action lazily creates
`output/<database>/run_<UTC timestamp>/`; individual stage folders are created only by
their writers. A completed full run covers:

```text
00_Run_Metadata              12_Synonyms_Sequences
01_Executive_Summary         13_Data_Profiling
02_Server_Database           14_Samples
03_Schemas                   15_Lineage
04_Tables                    16_Pipelines
05_Columns                   17_Data_Quality
06_Keys_Relationships        18_Risks_Uncertainties
07_Indexes_Constraints       19_Diagrams
08_Views                     20_Object_Documentation
09_Stored_Procedures         21_HTML_Report
10_Functions                 99_Git_Handoff
11_Triggers
```

Cancelled or failed attempts retain only the folders/evidence truthfully reached plus
`00_Run_Metadata` control files. They are never padded with placeholder folders.

Git export is a separate explicit action and creates
`git_export/MSSQL/<database>/run_<run id>/`. Before creating the destination, the
service requires a manifested run inside the configured output root and rejects:

- `.env`, credential files, configured secret values, or unredacted secret assignments;
- raw/unmasked sensitive evidence;
- symlinks, caches, temp directories, internal logs, or unsupported/binary files;
- any source path outside the configured output root or an existing destination.

Only `.csv`, `.html`, `.json`, `.md`, `.mmd`, `.sha256`, `.sql`, and `.txt` evidence or
presentation files are copied. The export contains no connection string or unrestricted
operational log and remains subject to operator review before source-control handoff.
