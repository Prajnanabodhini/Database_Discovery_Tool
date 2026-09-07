# v3.1.1 Scope Freeze — Do Not Change

The following are explicitly outside this hardening release.

Do not implement them while executing this pack:

- MariaDB discovery/documentation;
- PostgreSQL/MySQL/Oracle support;
- remote Web deployment;
- authentication system for the localhost dashboard;
- multi-user server mode;
- arbitrary SQL console;
- stored procedure execution;
- Agent job execution;
- PowerShell/CmdExec/SSIS execution;
- database writes;
- schema fixes;
- database performance tuning actions;
- migration generation;
- ETL execution;
- AI-generated SQL execution;
- automatic external-system traversal;
- raw evidence publication;
- unrelated UI redesign;
- replacement of Flask;
- full rewrite of `fullrun.py`;
- new database registry/service;
- cloud deployment;
- scheduled background discovery;
- MariaDB collector integration;
- SchoolERP Result Management application changes.

If an implementation change appears to require one of these, stop and document the dependency instead.
