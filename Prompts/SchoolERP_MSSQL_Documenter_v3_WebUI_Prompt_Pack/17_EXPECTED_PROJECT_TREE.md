# Expected Project Tree

```text
mssql_database_documenter/
├── main.py
├── run_dashboard.bat
├── run_metadata.bat
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
├── sql/
├── src/
│   └── mssql_database_documenter/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── connection.py
│       ├── safety.py
│       ├── metadata/
│       ├── profiling/
│       ├── relationships/
│       ├── lineage/
│       ├── analysis/
│       ├── reporting/
│       ├── comparison/
│       └── web/
│           ├── app.py
│           ├── api.py
│           ├── security.py
│           ├── job_manager.py
│           ├── file_browser.py
│           ├── renderers.py
│           ├── compare_api.py
│           ├── templates/
│           └── static/
└── tests/
```

The following should NOT exist until runtime:

```text
output/
git_export/
```
