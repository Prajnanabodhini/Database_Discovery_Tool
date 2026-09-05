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


def get_query(name: str) -> QuerySpec:
    for query in QUERIES:
        if query.name == name:
            return query
    raise KeyError(f"Unknown registered query: {name}")
