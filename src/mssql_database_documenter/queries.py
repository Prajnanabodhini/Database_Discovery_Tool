"""Static query registry for the offline safety gate and first connection check."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuerySpec:
    name: str
    stage: str
    sql: str
    columns: tuple[str, ...] = ()
    output_folder: str = ""
    output_name: str = ""
    feature_family: str = ""
    optional_setting: str = ""


QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        name="connection_identity",
        stage="connection",
        sql="""
            SELECT
                CAST(SERVERPROPERTY('ServerName') AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                SUSER_SNAME() AS login_name
        """,
    ),
    QuerySpec(
        name="server_capabilities",
        stage="connection",
        sql="""
            SELECT
                CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128)) AS product_version,
                CAST(SERVERPROPERTY('ProductLevel') AS nvarchar(128)) AS product_level,
                CAST(SERVERPROPERTY('Edition') AS nvarchar(256)) AS edition,
                CAST(SERVERPROPERTY('EngineEdition') AS int) AS engine_edition,
                CAST(SERVERPROPERTY('Collation') AS nvarchar(256)) AS server_collation
        """,
    ),
    QuerySpec(
        name="database_capabilities",
        stage="connection",
        sql="""
            SELECT
                d.name AS database_name,
                d.database_id,
                d.create_date,
                d.compatibility_level,
                d.collation_name,
                d.state_desc,
                d.recovery_model_desc,
                d.is_read_only,
                d.snapshot_isolation_state_desc,
                d.containment_desc,
                d.page_verify_option_desc
            FROM sys.databases AS d
            WHERE d.database_id = DB_ID()
        """,
    ),
)


METADATA_QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        name="schemas",
        stage="metadata",
        output_folder="03_Schemas",
        output_name="SCHEMA_CATALOGUE.csv",
        columns=("server_name", "database_name", "schema_id", "schema_name", "owner_name", "is_system_schema"),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.schema_id,
                s.name AS schema_name,
                USER_NAME(s.principal_id) AS owner_name,
                CASE WHEN s.name IN ('sys', 'INFORMATION_SCHEMA') THEN 1 ELSE 0 END AS is_system_schema
            FROM sys.schemas AS s
            ORDER BY s.name
        """,
    ),
    QuerySpec(
        name="tables",
        stage="metadata",
        output_folder="04_Tables",
        output_name="TABLE_CATALOGUE.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "object_id",
            "create_date", "modify_date", "is_ms_shipped", "temporal_type_desc",
            "history_schema_name", "history_table_name", "is_memory_optimized",
            "durability_desc", "lob_data_space_id", "filestream_data_space_id",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                t.object_id,
                t.create_date,
                t.modify_date,
                t.is_ms_shipped,
                t.temporal_type_desc,
                hs.name AS history_schema_name,
                ht.name AS history_table_name,
                t.is_memory_optimized,
                t.durability_desc,
                t.lob_data_space_id,
                t.filestream_data_space_id
            FROM sys.tables AS t
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            LEFT JOIN sys.tables AS ht ON ht.object_id = t.history_table_id
            LEFT JOIN sys.schemas AS hs ON hs.schema_id = ht.schema_id
            ORDER BY s.name, t.name
        """,
    ),
    QuerySpec(
        name="columns",
        stage="metadata",
        output_folder="05_Columns",
        output_name="COLUMN_CATALOGUE.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "object_type",
            "object_id", "column_id", "column_name", "type_schema_name", "data_type",
            "max_length", "precision", "scale", "collation_name", "is_nullable",
            "is_identity", "identity_seed", "identity_increment", "is_computed",
            "computed_definition", "is_persisted", "default_name", "default_definition",
            "is_sparse", "is_rowguidcol", "is_filestream", "is_hidden", "generated_always_type_desc",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                o.name AS object_name,
                o.type_desc AS object_type,
                o.object_id,
                c.column_id,
                c.name AS column_name,
                ts.name AS type_schema_name,
                ty.name AS data_type,
                c.max_length,
                c.precision,
                c.scale,
                c.collation_name,
                c.is_nullable,
                c.is_identity,
                CAST(ic.seed_value AS nvarchar(128)) AS identity_seed,
                CAST(ic.increment_value AS nvarchar(128)) AS identity_increment,
                c.is_computed,
                cc.definition AS computed_definition,
                cc.is_persisted,
                dc.name AS default_name,
                dc.definition AS default_definition,
                c.is_sparse,
                c.is_rowguidcol,
                c.is_filestream,
                c.is_hidden,
                c.generated_always_type_desc
            FROM sys.objects AS o
            JOIN sys.schemas AS s ON s.schema_id = o.schema_id
            JOIN sys.columns AS c ON c.object_id = o.object_id
            JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
            JOIN sys.schemas AS ts ON ts.schema_id = ty.schema_id
            LEFT JOIN sys.identity_columns AS ic
                ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            LEFT JOIN sys.computed_columns AS cc
                ON cc.object_id = c.object_id AND cc.column_id = c.column_id
            LEFT JOIN sys.default_constraints AS dc ON dc.object_id = c.default_object_id
            WHERE o.type IN ('U', 'V')
            ORDER BY s.name, o.name, c.column_id
        """,
    ),
    QuerySpec(
        name="primary_keys",
        stage="metadata",
        output_folder="06_Keys_Relationships",
        output_name="PRIMARY_KEYS.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "constraint_name",
            "index_name", "index_type_desc", "is_system_named", "key_ordinal", "column_name",
            "is_descending_key",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                kc.name AS constraint_name,
                i.name AS index_name,
                i.type_desc AS index_type_desc,
                kc.is_system_named,
                ic.key_ordinal,
                c.name AS column_name,
                ic.is_descending_key
            FROM sys.key_constraints AS kc
            JOIN sys.tables AS t ON t.object_id = kc.parent_object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            JOIN sys.indexes AS i
                ON i.object_id = kc.parent_object_id AND i.index_id = kc.unique_index_id
            JOIN sys.index_columns AS ic
                ON ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.key_ordinal > 0
            JOIN sys.columns AS c
                ON c.object_id = ic.object_id AND c.column_id = ic.column_id
            WHERE kc.type = 'PK'
            ORDER BY s.name, t.name, ic.key_ordinal
        """,
    ),
    QuerySpec(
        name="foreign_keys",
        stage="metadata",
        output_folder="06_Keys_Relationships",
        output_name="FOREIGN_KEYS.csv",
        columns=(
            "server_name", "database_name", "source_schema", "source_object", "constraint_name",
            "constraint_column_id", "source_column", "target_schema", "target_object", "target_column",
            "delete_action", "update_action", "is_disabled", "is_not_trusted", "is_not_for_replication",
            "is_system_named",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                ss.name AS source_schema,
                st.name AS source_object,
                fk.name AS constraint_name,
                fkc.constraint_column_id,
                sc.name AS source_column,
                ts.name AS target_schema,
                tt.name AS target_object,
                tc.name AS target_column,
                fk.delete_referential_action_desc AS delete_action,
                fk.update_referential_action_desc AS update_action,
                fk.is_disabled,
                fk.is_not_trusted,
                fk.is_not_for_replication,
                fk.is_system_named
            FROM sys.foreign_keys AS fk
            JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
            JOIN sys.tables AS st ON st.object_id = fk.parent_object_id
            JOIN sys.schemas AS ss ON ss.schema_id = st.schema_id
            JOIN sys.columns AS sc
                ON sc.object_id = fkc.parent_object_id AND sc.column_id = fkc.parent_column_id
            JOIN sys.tables AS tt ON tt.object_id = fk.referenced_object_id
            JOIN sys.schemas AS ts ON ts.schema_id = tt.schema_id
            JOIN sys.columns AS tc
                ON tc.object_id = fkc.referenced_object_id AND tc.column_id = fkc.referenced_column_id
            ORDER BY ss.name, st.name, fk.name, fkc.constraint_column_id
        """,
    ),
    QuerySpec(
        name="indexes",
        stage="metadata",
        output_folder="07_Indexes_Constraints",
        output_name="INDEX_CATALOGUE.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "index_name", "index_id",
            "index_type_desc", "is_unique", "is_primary_key", "is_unique_constraint", "has_filter",
            "filter_definition", "is_disabled", "fill_factor", "data_space_name", "column_ordinal",
            "key_ordinal", "column_name", "is_descending_key", "is_included_column",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                o.name AS object_name,
                i.name AS index_name,
                i.index_id,
                i.type_desc AS index_type_desc,
                i.is_unique,
                i.is_primary_key,
                i.is_unique_constraint,
                i.has_filter,
                i.filter_definition,
                i.is_disabled,
                i.fill_factor,
                ds.name AS data_space_name,
                ic.index_column_id AS column_ordinal,
                ic.key_ordinal,
                c.name AS column_name,
                ic.is_descending_key,
                ic.is_included_column
            FROM sys.objects AS o
            JOIN sys.schemas AS s ON s.schema_id = o.schema_id
            JOIN sys.indexes AS i ON i.object_id = o.object_id
            LEFT JOIN sys.data_spaces AS ds ON ds.data_space_id = i.data_space_id
            LEFT JOIN sys.index_columns AS ic
                ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            LEFT JOIN sys.columns AS c
                ON c.object_id = ic.object_id AND c.column_id = ic.column_id
            WHERE o.type IN ('U', 'V') AND i.index_id > 0
            ORDER BY s.name, o.name, i.index_id, ic.index_column_id
        """,
    ),
    QuerySpec(
        name="constraints",
        stage="metadata",
        output_folder="07_Indexes_Constraints",
        output_name="CONSTRAINT_CATALOGUE.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "constraint_name",
            "constraint_type", "column_name", "definition", "is_disabled", "is_not_trusted",
            "is_system_named",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                cc.name AS constraint_name,
                CAST('CHECK' AS nvarchar(32)) AS constraint_type,
                col.name AS column_name,
                cc.definition,
                cc.is_disabled,
                cc.is_not_trusted,
                cc.is_system_named
            FROM sys.check_constraints AS cc
            JOIN sys.tables AS t ON t.object_id = cc.parent_object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            LEFT JOIN sys.columns AS col
                ON col.object_id = cc.parent_object_id AND col.column_id = cc.parent_column_id
            UNION ALL
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                dc.name AS constraint_name,
                CAST('DEFAULT' AS nvarchar(32)) AS constraint_type,
                col.name AS column_name,
                dc.definition,
                CAST(0 AS bit) AS is_disabled,
                CAST(0 AS bit) AS is_not_trusted,
                dc.is_system_named
            FROM sys.default_constraints AS dc
            JOIN sys.tables AS t ON t.object_id = dc.parent_object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            JOIN sys.columns AS col
                ON col.object_id = dc.parent_object_id AND col.column_id = dc.parent_column_id
            UNION ALL
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                kc.name AS constraint_name,
                CAST(kc.type_desc AS nvarchar(32)) AS constraint_type,
                CAST(NULL AS sysname) AS column_name,
                CAST(NULL AS nvarchar(max)) AS definition,
                CAST(0 AS bit) AS is_disabled,
                CAST(0 AS bit) AS is_not_trusted,
                kc.is_system_named
            FROM sys.key_constraints AS kc
            JOIN sys.tables AS t ON t.object_id = kc.parent_object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
        """,
    ),
    QuerySpec(
        name="extended_properties",
        stage="metadata",
        output_folder="05_Columns",
        output_name="EXTENDED_PROPERTIES.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "column_name",
            "property_name", "property_value", "class_desc", "major_id", "minor_id",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                o.name AS object_name,
                c.name AS column_name,
                ep.name AS property_name,
                CAST(ep.value AS nvarchar(max)) AS property_value,
                ep.class_desc,
                ep.major_id,
                ep.minor_id
            FROM sys.extended_properties AS ep
            LEFT JOIN sys.objects AS o ON o.object_id = ep.major_id AND ep.class = 1
            LEFT JOIN sys.schemas AS s ON s.schema_id = o.schema_id
            LEFT JOIN sys.columns AS c
                ON c.object_id = ep.major_id AND c.column_id = ep.minor_id AND ep.minor_id > 0
            WHERE ep.class = 1
            ORDER BY s.name, o.name, ep.minor_id, ep.name
        """,
    ),
    QuerySpec(
        name="table_sizes",
        stage="metadata",
        output_folder="04_Tables",
        output_name="TABLE_SIZE_PROFILE.csv",
        columns=(
            "server_name", "database_name", "schema_name", "object_name", "row_count_type",
            "row_count", "reserved_kb", "used_kb", "data_kb", "index_kb", "unused_kb",
        ),
        sql="""
            SELECT
                CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                DB_NAME() AS database_name,
                s.name AS schema_name,
                t.name AS object_name,
                CAST('ESTIMATED' AS nvarchar(16)) AS row_count_type,
                SUM(CASE WHEN ps.index_id IN (0, 1) THEN ps.row_count ELSE 0 END) AS row_count,
                SUM(ps.reserved_page_count) * 8 AS reserved_kb,
                SUM(ps.used_page_count) * 8 AS used_kb,
                SUM(CASE WHEN ps.index_id IN (0, 1) THEN ps.in_row_data_page_count + ps.lob_used_page_count + ps.row_overflow_used_page_count ELSE 0 END) * 8 AS data_kb,
                SUM(CASE WHEN ps.index_id > 1 THEN ps.used_page_count ELSE 0 END) * 8 AS index_kb,
                (SUM(ps.reserved_page_count) - SUM(ps.used_page_count)) * 8 AS unused_kb
            FROM sys.tables AS t
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            JOIN sys.dm_db_partition_stats AS ps ON ps.object_id = t.object_id
            GROUP BY s.name, t.name
            ORDER BY reserved_kb DESC, s.name, t.name
        """,
    ),
)


METADATA_COMPLETENESS_QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        name="database_files", stage="metadata", output_folder="02_Server_Database",
        output_name="DATABASE_FILES.csv", feature_family="database_files",
        columns=("server_name", "database_name", "file_id", "file_name", "file_type", "filegroup_name", "state_desc", "size_kb", "max_size_kb", "growth", "is_percent_growth", "is_read_only", "is_sparse"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, df.file_id, df.name AS file_name,
                   df.type_desc AS file_type, fg.name AS filegroup_name, df.state_desc,
                   CONVERT(bigint, df.size) * 8 AS size_kb,
                   CASE WHEN df.max_size = -1 THEN CONVERT(bigint, -1) ELSE CONVERT(bigint, df.max_size) * 8 END AS max_size_kb,
                   df.growth, df.is_percent_growth, df.is_read_only, df.is_sparse
            FROM sys.database_files AS df
            LEFT JOIN sys.filegroups AS fg ON fg.data_space_id = df.data_space_id
            ORDER BY df.file_id
        """,
    ),
    QuerySpec(
        name="filegroups", stage="metadata", output_folder="02_Server_Database",
        output_name="FILEGROUP_CATALOGUE.csv", feature_family="filegroups",
        columns=("server_name", "database_name", "data_space_id", "filegroup_name", "type_desc", "is_default", "is_read_only", "file_count", "total_size_kb"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, fg.data_space_id, fg.name AS filegroup_name,
                   fg.type_desc, fg.is_default, fg.is_read_only,
                   COUNT(df.file_id) AS file_count,
                   COALESCE(SUM(CONVERT(bigint, df.size) * 8), 0) AS total_size_kb
            FROM sys.filegroups AS fg
            LEFT JOIN sys.database_files AS df ON df.data_space_id = fg.data_space_id
            GROUP BY fg.data_space_id, fg.name, fg.type_desc, fg.is_default, fg.is_read_only
            ORDER BY fg.data_space_id
        """,
    ),
    QuerySpec(
        name="partition_functions", stage="metadata", output_folder="07_Indexes_Constraints",
        output_name="PARTITION_FUNCTIONS.csv", feature_family="partition_functions",
        columns=("server_name", "database_name", "function_id", "function_name", "type_desc", "boundary_value_on_right", "fanout", "parameter_id", "type_schema_name", "data_type", "max_length", "precision", "scale", "collation_name"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, pf.function_id, pf.name AS function_name,
                   pf.type_desc, pf.boundary_value_on_right, pf.fanout, pp.parameter_id,
                   ts.name AS type_schema_name, ty.name AS data_type, pp.max_length,
                   pp.precision, pp.scale, pp.collation_name
            FROM sys.partition_functions AS pf
            JOIN sys.partition_parameters AS pp ON pp.function_id = pf.function_id
            JOIN sys.types AS ty ON ty.user_type_id = pp.user_type_id
            JOIN sys.schemas AS ts ON ts.schema_id = ty.schema_id
            ORDER BY pf.name, pp.parameter_id
        """,
    ),
    QuerySpec(
        name="partition_schemes", stage="metadata", output_folder="07_Indexes_Constraints",
        output_name="PARTITION_SCHEMES.csv", feature_family="partition_schemes",
        columns=("server_name", "database_name", "data_space_id", "scheme_name", "function_id", "function_name", "destination_id", "destination_data_space_id", "filegroup_name"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, ps.data_space_id, ps.name AS scheme_name,
                   ps.function_id, pf.name AS function_name, dds.destination_id,
                   dds.data_space_id AS destination_data_space_id, fg.name AS filegroup_name
            FROM sys.partition_schemes AS ps
            JOIN sys.partition_functions AS pf ON pf.function_id = ps.function_id
            JOIN sys.destination_data_spaces AS dds ON dds.partition_scheme_id = ps.data_space_id
            LEFT JOIN sys.filegroups AS fg ON fg.data_space_id = dds.data_space_id
            ORDER BY ps.name, dds.destination_id
        """,
    ),
    QuerySpec(
        name="partition_compression", stage="metadata", output_folder="04_Tables",
        output_name="PARTITION_COMPRESSION.csv", feature_family="partition_compression",
        columns=("server_name", "database_name", "schema_name", "object_name", "index_name", "index_id", "partition_number", "row_count", "data_compression", "data_space_name"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, s.name AS schema_name, t.name AS object_name,
                   i.name AS index_name, p.index_id, p.partition_number, p.rows AS row_count,
                   p.data_compression_desc AS data_compression, ds.name AS data_space_name
            FROM sys.tables AS t
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            JOIN sys.partitions AS p ON p.object_id = t.object_id
            JOIN sys.indexes AS i ON i.object_id = p.object_id AND i.index_id = p.index_id
            LEFT JOIN sys.partition_schemes AS ps ON ps.data_space_id = i.data_space_id
            LEFT JOIN sys.destination_data_spaces AS dds
              ON dds.partition_scheme_id = ps.data_space_id AND dds.destination_id = p.partition_number
            LEFT JOIN sys.data_spaces AS ds ON ds.data_space_id = COALESCE(dds.data_space_id, i.data_space_id)
            ORDER BY s.name, t.name, p.index_id, p.partition_number
        """,
    ),
    QuerySpec(
        name="user_defined_types", stage="metadata", output_folder="05_Columns",
        output_name="USER_DEFINED_TYPES.csv", feature_family="user_defined_types",
        columns=("server_name", "database_name", "type_schema_name", "type_name", "user_type_id", "system_type_name", "max_length", "precision", "scale", "collation_name", "is_nullable", "is_table_type", "is_assembly_type", "table_type_object_id"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, s.name AS type_schema_name, ty.name AS type_name,
                   ty.user_type_id, base.name AS system_type_name, ty.max_length, ty.precision,
                   ty.scale, ty.collation_name, ty.is_nullable, ty.is_table_type,
                   ty.is_assembly_type, tt.type_table_object_id AS table_type_object_id
            FROM sys.types AS ty
            JOIN sys.schemas AS s ON s.schema_id = ty.schema_id
            LEFT JOIN sys.types AS base
              ON base.user_type_id = ty.system_type_id AND base.user_type_id = base.system_type_id
            LEFT JOIN sys.table_types AS tt ON tt.user_type_id = ty.user_type_id
            WHERE ty.is_user_defined = 1 OR ty.is_table_type = 1
            ORDER BY s.name, ty.name
        """,
    ),
    QuerySpec(
        name="statistics", stage="metadata", output_folder="07_Indexes_Constraints",
        output_name="STATISTICS_CATALOGUE.csv", feature_family="statistics",
        columns=("server_name", "database_name", "schema_name", "object_name", "statistics_name", "stats_id", "auto_created", "user_created", "no_recompute", "has_filter", "filter_definition", "stats_column_id", "column_id", "column_name"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, s.name AS schema_name, o.name AS object_name,
                   st.name AS statistics_name, st.stats_id, st.auto_created, st.user_created,
                   st.no_recompute, st.has_filter, st.filter_definition, sc.stats_column_id,
                   sc.column_id, c.name AS column_name
            FROM sys.stats AS st
            JOIN sys.objects AS o ON o.object_id = st.object_id
            JOIN sys.schemas AS s ON s.schema_id = o.schema_id
            LEFT JOIN sys.stats_columns AS sc ON sc.object_id = st.object_id AND sc.stats_id = st.stats_id
            LEFT JOIN sys.columns AS c ON c.object_id = sc.object_id AND c.column_id = sc.column_id
            WHERE o.type IN ('U', 'V')
            ORDER BY s.name, o.name, st.stats_id, sc.stats_column_id
        """,
    ),
    QuerySpec(
        name="fulltext_catalogs", stage="metadata", output_folder="07_Indexes_Constraints",
        output_name="FULLTEXT_CATALOGUES.csv", feature_family="fulltext_catalogs",
        columns=("server_name", "database_name", "fulltext_catalog_id", "catalog_name", "is_default", "is_accent_sensitivity_on", "is_importing"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, fc.fulltext_catalog_id, fc.name AS catalog_name,
                   fc.is_default, fc.is_accent_sensitivity_on, fc.is_importing
            FROM sys.fulltext_catalogs AS fc
            ORDER BY fc.name
        """,
    ),
    QuerySpec(
        name="fulltext_indexes", stage="metadata", output_folder="07_Indexes_Constraints",
        output_name="FULLTEXT_INDEXES.csv", feature_family="fulltext_indexes",
        columns=("server_name", "database_name", "schema_name", "object_name", "object_id", "unique_index_name", "catalog_name", "is_enabled", "change_tracking_state", "has_crawl_completed", "crawl_type"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, s.name AS schema_name, t.name AS object_name,
                   fi.object_id, i.name AS unique_index_name, fc.name AS catalog_name,
                   fi.is_enabled, fi.change_tracking_state_desc AS change_tracking_state,
                   fi.has_crawl_completed, fi.crawl_type_desc AS crawl_type
            FROM sys.fulltext_indexes AS fi
            JOIN sys.tables AS t ON t.object_id = fi.object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            LEFT JOIN sys.indexes AS i ON i.object_id = fi.object_id AND i.index_id = fi.unique_index_id
            LEFT JOIN sys.fulltext_catalogs AS fc ON fc.fulltext_catalog_id = fi.fulltext_catalog_id
            ORDER BY s.name, t.name
        """,
    ),
    QuerySpec(
        name="cdc_status", stage="metadata", output_folder="02_Server_Database",
        output_name="CDC_STATUS.csv", feature_family="cdc_status",
        columns=("server_name", "database_name", "scope", "schema_name", "object_name", "is_cdc_enabled", "is_tracked_by_cdc"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   d.name AS database_name, CAST('DATABASE' AS nvarchar(16)) AS scope,
                   CAST(NULL AS sysname) AS schema_name, CAST(NULL AS sysname) AS object_name,
                   d.is_cdc_enabled, CAST(NULL AS bit) AS is_tracked_by_cdc
            FROM sys.databases AS d
            WHERE d.database_id = DB_ID() AND d.is_cdc_enabled = 1
            UNION ALL
            SELECT CAST('[SANITIZED]' AS nvarchar(256)), DB_NAME(), CAST('TABLE' AS nvarchar(16)),
                   s.name, t.name, CAST(1 AS bit), t.is_tracked_by_cdc
            FROM sys.tables AS t
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            WHERE t.is_tracked_by_cdc = 1
            ORDER BY scope, schema_name, object_name
        """,
    ),
    QuerySpec(
        name="change_tracking_status", stage="metadata", output_folder="02_Server_Database",
        output_name="CHANGE_TRACKING_STATUS.csv", feature_family="change_tracking_status",
        columns=("server_name", "database_name", "scope", "schema_name", "object_name", "is_auto_cleanup_on", "retention_period", "retention_period_units", "is_track_columns_updated_on", "begin_version", "cleanup_version", "min_valid_version"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, CAST('DATABASE' AS nvarchar(16)) AS scope,
                   CAST(NULL AS sysname) AS schema_name, CAST(NULL AS sysname) AS object_name,
                   ctd.is_auto_cleanup_on, ctd.retention_period,
                   ctd.retention_period_units_desc AS retention_period_units,
                   CAST(NULL AS bit) AS is_track_columns_updated_on,
                   CAST(NULL AS bigint) AS begin_version, CAST(NULL AS bigint) AS cleanup_version,
                   CAST(NULL AS bigint) AS min_valid_version
            FROM sys.change_tracking_databases AS ctd
            WHERE ctd.database_id = DB_ID()
            UNION ALL
            SELECT CAST('[SANITIZED]' AS nvarchar(256)), DB_NAME(), CAST('TABLE' AS nvarchar(16)),
                   s.name, t.name, ctd.is_auto_cleanup_on, ctd.retention_period,
                   ctd.retention_period_units_desc, ctt.is_track_columns_updated_on,
                   ctt.begin_version, ctt.cleanup_version, ctt.min_valid_version
            FROM sys.change_tracking_tables AS ctt
            JOIN sys.tables AS t ON t.object_id = ctt.object_id
            JOIN sys.schemas AS s ON s.schema_id = t.schema_id
            JOIN sys.change_tracking_databases AS ctd ON ctd.database_id = DB_ID()
            ORDER BY scope, schema_name, object_name
        """,
    ),
    QuerySpec(
        name="database_scoped_configurations", stage="metadata", output_folder="02_Server_Database",
        output_name="DATABASE_SCOPED_CONFIGURATIONS.csv", feature_family="database_scoped_configurations",
        columns=("server_name", "database_name", "configuration_id", "configuration_name", "configured_value", "value_for_secondary"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, configuration_id, name AS configuration_name,
                   CONVERT(nvarchar(4000), value) AS configured_value,
                   CONVERT(nvarchar(4000), value_for_secondary) AS value_for_secondary
            FROM sys.database_scoped_configurations
            ORDER BY configuration_id
        """,
    ),
    QuerySpec(
        name="xml_schema_collections", stage="metadata", output_folder="05_Columns",
        output_name="XML_SCHEMA_COLLECTIONS.csv", feature_family="xml_schema_collections",
        columns=("server_name", "database_name", "xml_collection_id", "schema_name", "collection_name", "principal_id", "create_date", "modify_date"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, xsc.xml_collection_id, s.name AS schema_name,
                   xsc.name AS collection_name, xsc.principal_id, xsc.create_date, xsc.modify_date
            FROM sys.xml_schema_collections AS xsc
            JOIN sys.schemas AS s ON s.schema_id = xsc.schema_id
            WHERE xsc.xml_collection_id > 1
            ORDER BY s.name, xsc.name
        """,
    ),
)


SECURITY_METADATA_QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        name="security_principals", stage="metadata", output_folder="02_Server_Database",
        output_name="SECURITY_PRINCIPALS.csv", feature_family="security_principals",
        optional_setting="discover_security_metadata",
        columns=("server_name", "database_name", "principal_id", "principal_type", "authentication_type", "principal_name_sha256", "default_schema_name", "create_date", "modify_date", "is_fixed_role"),
        sql="""
            SELECT CAST('[SANITIZED]' AS nvarchar(256)) AS server_name,
                   DB_NAME() AS database_name, dp.principal_id,
                   dp.type_desc AS principal_type,
                   dp.authentication_type_desc AS authentication_type,
                   CONVERT(varchar(64), HASHBYTES('SHA2_256', CONVERT(varbinary(max), dp.name)), 2) AS principal_name_sha256,
                   dp.default_schema_name, dp.create_date, dp.modify_date, dp.is_fixed_role
            FROM sys.database_principals AS dp
            WHERE dp.principal_id > 4
            ORDER BY dp.principal_id
        """,
    ),
)


METADATA_QUERIES = METADATA_QUERIES + METADATA_COMPLETENESS_QUERIES


def get_query(name: str) -> QuerySpec:
    for query in QUERIES:
        if query.name == name:
            return query
    raise KeyError(f"Unknown registered query: {name}")
