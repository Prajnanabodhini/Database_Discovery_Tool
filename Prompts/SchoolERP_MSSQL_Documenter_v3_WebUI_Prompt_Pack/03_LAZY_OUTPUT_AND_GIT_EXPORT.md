# Prompt — Lazy Output and Git Export Lifecycle

Fix all eager folder generation.

Source scaffold must not contain runtime evidence directories.

Configured paths:
- OUTPUT_ROOT
- GIT_EXPORT_ROOT

Rules:

1. No output directory creation on import.
2. No output directory creation on Web UI startup.
3. No output directory creation on dry-run.
4. `test-connection` must not create a run directory.
5. A real discovery run creates:
   `output/<db>/run_<timestamp>/`
6. Only the run's required subfolders are created as needed.
7. Git export root is created only by explicit Git Export action.
8. No placeholder/fake output artifacts.
9. UI handles absent roots gracefully.
10. Tests prove these behaviors.
