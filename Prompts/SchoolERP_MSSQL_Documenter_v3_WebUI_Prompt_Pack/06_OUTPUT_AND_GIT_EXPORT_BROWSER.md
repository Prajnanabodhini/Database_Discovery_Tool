# Prompt — Browse Output and Git Export in HTML

Create a dual-root browser.

Root choices:
1. Output
2. Git Export

Scan filesystem only under configured roots.

Show:
- database
- run
- directories/files
- breadcrumbs
- size
- modified time
- type
- search/filter

Security:
- resolve paths
- reject absolute escapes
- reject `..`
- reject symlink escape
- never browse source/.env/log folders outside roots

Missing roots show clean empty-state message.
