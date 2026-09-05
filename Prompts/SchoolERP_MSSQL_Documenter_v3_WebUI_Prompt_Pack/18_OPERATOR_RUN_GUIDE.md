# Operator Run Guide

After implementation:

1. Create/activate venv.
2. Install requirements.
3. Copy `.env.example` to `.env`.
4. Configure one MSSQL DB for first validation.
5. Run:

```bash
python main.py
```

Browser should open local dashboard.

Recommended first actions:

1. Dry Run
2. Test Connection
3. Metadata
4. review output
5. Metadata + Logic
6. review
7. Safe Profile
8. review
9. Git Export

Only after validation use multiple DBs.

Use compare page to choose:
- Run A
- Run B
- optional Run C

Never expose the local web server to network interfaces unless a separate security review explicitly authorizes it.
