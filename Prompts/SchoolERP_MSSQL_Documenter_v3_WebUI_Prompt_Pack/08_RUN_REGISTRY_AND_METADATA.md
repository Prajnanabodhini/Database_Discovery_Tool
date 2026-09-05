# Prompt — Run Registry

Build run discovery by scanning real manifests in output folders.

Each run entry:
- run ID
- DB
- sanitized server
- timestamp
- mode
- status
- tool version
- SQL version
- profile settings
- coverage
- error count
- warning count
- path

Do not require a separate mutable database just to track runs.

Support partially completed runs.
