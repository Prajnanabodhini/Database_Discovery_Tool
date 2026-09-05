"""Static programmable-object and dependency catalog queries."""

from __future__ import annotations

from .queries import QuerySpec


PROGRAMMABLE_QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        "views", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, v.name AS object_name, v.object_id, v.create_date,
               v.modify_date, v.is_ms_shipped, v.is_date_correlation_view,
               m.uses_ansi_nulls, m.uses_quoted_identifier, m.is_schema_bound,
               m.is_recompiled, m.null_on_null_input, m.execute_as_principal_id,
               m.definition
        FROM sys.views AS v
        JOIN sys.schemas AS s ON s.schema_id = v.schema_id
        LEFT JOIN sys.sql_modules AS m ON m.object_id = v.object_id
        ORDER BY s.name, v.name
        """,
    ),
    QuerySpec(
        "procedures", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, p.name AS object_name, p.object_id, p.create_date,
               p.modify_date, p.is_ms_shipped, p.is_auto_executed, p.is_execution_replicated,
               m.uses_ansi_nulls, m.uses_quoted_identifier, m.is_schema_bound,
               m.is_recompiled, m.null_on_null_input, m.execute_as_principal_id,
               m.definition
        FROM sys.procedures AS p
        JOIN sys.schemas AS s ON s.schema_id = p.schema_id
        LEFT JOIN sys.sql_modules AS m ON m.object_id = p.object_id
        ORDER BY s.name, p.name
        """,
    ),
    QuerySpec(
        "functions", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, o.name AS object_name, o.object_id, o.type,
               o.type_desc, o.create_date, o.modify_date, o.is_ms_shipped,
               m.uses_ansi_nulls, m.uses_quoted_identifier, m.is_schema_bound,
               m.is_recompiled, m.null_on_null_input, m.execute_as_principal_id,
               m.definition
        FROM sys.objects AS o
        JOIN sys.schemas AS s ON s.schema_id = o.schema_id
        LEFT JOIN sys.sql_modules AS m ON m.object_id = o.object_id
        WHERE o.type IN ('FN', 'IF', 'TF', 'FS', 'FT')
        ORDER BY s.name, o.name
        """,
    ),
    QuerySpec(
        "triggers", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               OBJECT_SCHEMA_NAME(tr.parent_id) AS parent_schema_name,
               OBJECT_NAME(tr.parent_id) AS parent_object_name,
               tr.name AS object_name, tr.object_id, tr.parent_class_desc, tr.type_desc,
               tr.create_date, tr.modify_date, tr.is_ms_shipped, tr.is_disabled,
               tr.is_not_for_replication, tr.is_instead_of_trigger, m.definition
        FROM sys.triggers AS tr
        LEFT JOIN sys.sql_modules AS m ON m.object_id = tr.object_id
        ORDER BY parent_schema_name, parent_object_name, tr.name
        """,
    ),
    QuerySpec(
        "synonyms", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, sy.name AS object_name, sy.object_id,
               sy.create_date, sy.modify_date, sy.base_object_name
        FROM sys.synonyms AS sy
        JOIN sys.schemas AS s ON s.schema_id = sy.schema_id
        ORDER BY s.name, sy.name
        """,
    ),
    QuerySpec(
        "sequences", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, seq.name AS object_name, seq.object_id,
               TYPE_NAME(seq.user_type_id) AS data_type,
               CAST(seq.start_value AS nvarchar(128)) AS start_value,
               CAST(seq.increment AS nvarchar(128)) AS increment_value,
               CAST(seq.minimum_value AS nvarchar(128)) AS minimum_value,
               CAST(seq.maximum_value AS nvarchar(128)) AS maximum_value,
               CAST(seq.current_value AS nvarchar(128)) AS current_value,
               seq.is_cycling, seq.is_cached, seq.cache_size, seq.is_exhausted,
               seq.create_date, seq.modify_date
        FROM sys.sequences AS seq
        JOIN sys.schemas AS s ON s.schema_id = seq.schema_id
        ORDER BY s.name, seq.name
        """,
    ),
    QuerySpec(
        "parameters", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name, DB_NAME() AS database_name,
               s.name AS schema_name, o.name AS object_name, o.type_desc AS object_type,
               p.parameter_id, p.name AS parameter_name, TYPE_NAME(p.user_type_id) AS data_type,
               p.max_length, p.precision, p.scale, p.is_output, p.has_default_value,
               CAST(p.default_value AS nvarchar(4000)) AS default_value, p.is_readonly
        FROM sys.parameters AS p
        JOIN sys.objects AS o ON o.object_id = p.object_id
        JOIN sys.schemas AS s ON s.schema_id = o.schema_id
        ORDER BY s.name, o.name, p.parameter_id
        """,
    ),
    QuerySpec(
        "dependencies", "programmable", """
        SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS source_server,
               DB_NAME() AS source_database, ss.name AS source_schema,
               so.name AS source_object, so.type_desc AS source_type,
               sed.referencing_minor_id AS source_column_id,
               sed.referenced_server_name AS target_server,
               sed.referenced_database_name AS target_database,
               sed.referenced_schema_name AS target_schema,
               sed.referenced_entity_name AS target_object,
               tc.name AS target_column,
               sed.is_schema_bound_reference, sed.is_caller_dependent,
               sed.is_ambiguous, sed.referenced_id
        FROM sys.sql_expression_dependencies AS sed
        JOIN sys.objects AS so ON so.object_id = sed.referencing_id
        JOIN sys.schemas AS ss ON ss.schema_id = so.schema_id
        LEFT JOIN sys.columns AS tc
          ON tc.object_id = sed.referenced_id AND tc.column_id = sed.referenced_minor_id
        ORDER BY ss.name, so.name, sed.referencing_minor_id
        """,
    ),
)


SQL_AGENT_QUERY = QuerySpec(
    "sql_agent_jobs", "programmable", """
    SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
           j.name AS job_name, j.enabled AS job_enabled, j.description,
           js.step_id, js.step_name, js.subsystem,
           CONVERT(varchar(64), HASHBYTES('SHA2_256', CONVERT(varbinary(max), js.command)), 2) AS command_sha256,
           js.database_name, js.on_success_action, js.on_fail_action,
           sch.name AS schedule_name, sch.enabled AS schedule_enabled,
           sch.freq_type, sch.freq_interval, sch.active_start_date, sch.active_start_time
    FROM msdb.dbo.sysjobs AS j
    LEFT JOIN msdb.dbo.sysjobsteps AS js ON js.job_id = j.job_id
    LEFT JOIN msdb.dbo.sysjobschedules AS jsch ON jsch.job_id = j.job_id
    LEFT JOIN msdb.dbo.sysschedules AS sch ON sch.schedule_id = jsch.schedule_id
    ORDER BY j.name, js.step_id
    """,
)
