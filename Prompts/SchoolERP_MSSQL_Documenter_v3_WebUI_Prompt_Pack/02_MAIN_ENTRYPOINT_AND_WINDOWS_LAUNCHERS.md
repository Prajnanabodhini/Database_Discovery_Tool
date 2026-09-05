# Prompt — Implement the Main Entry Point

Require a root-level `main.py`.

It must be small and contain only command routing/startup.

Required commands:

```bash
python main.py
python main.py web
python main.py test-connection
python main.py cli --mode metadata
python main.py cli --mode metadata+logic
python main.py cli --mode safe-profile
python main.py cli --mode full-readonly
python main.py --help
```

`python main.py` defaults to Web UI.

Create:
- `run_dashboard.bat`
- `run_metadata.bat`

The BAT files must:
- use the local virtual environment Python if present,
- otherwise use `python`,
- never contain credentials,
- preserve exit code,
- pause only when useful for an error.

Add launcher tests.
