# Samples Prompt
Create deterministic masked samples for every accessible table/view (default TOP N by PK where practical), with headers and sample metadata. Avoid ORDER BY NEWID on large tables. Never sample procedures/triggers through execution.
