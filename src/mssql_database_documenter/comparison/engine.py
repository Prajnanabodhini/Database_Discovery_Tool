"""Comparison orchestration across two or three actual run snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import hashlib
import json
from typing import Any

from .diff import compare_rows
from .loaders import RunSnapshot, load_run


@dataclass(frozen=True, slots=True)
class CatalogueSpec:
    path: str
    keys: tuple[str, ...]
    fields: tuple[str, ...]
    numeric: tuple[str, ...] = ()
    definition: str | None = None


CATALOGUES: dict[str, CatalogueSpec] = {
    "schemas": CatalogueSpec("03_Schemas/SCHEMA_CATALOGUE.csv", ("schema_name",), ("owner_name",)),
    "tables": CatalogueSpec("04_Tables/TABLE_CATALOGUE.csv", ("schema_name", "object_name"), ("temporal_type_desc", "is_memory_optimized", "inferred_category")),
    "columns": CatalogueSpec("05_Columns/COLUMN_CATALOGUE.csv", ("schema_name", "object_name", "column_name"), ("data_type", "max_length", "precision", "scale", "is_nullable", "is_identity", "is_computed"), ("max_length", "precision", "scale")),
    "primary_keys": CatalogueSpec("06_Keys_Relationships/PRIMARY_KEYS.csv", ("schema_name", "object_name", "constraint_name", "key_ordinal"), ("column_name", "is_descending_key")),
    "foreign_keys": CatalogueSpec("06_Keys_Relationships/FOREIGN_KEYS.csv", ("source_schema", "source_object", "constraint_name", "constraint_column_id"), ("source_column", "target_schema", "target_object", "target_column", "delete_action", "update_action", "is_disabled", "is_not_trusted")),
    "inferred_relationships": CatalogueSpec("06_Keys_Relationships/INFERRED_RELATIONSHIPS.csv", ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column"), ("classification", "confidence", "evidence")),
    "indexes": CatalogueSpec("07_Indexes_Constraints/INDEX_CATALOGUE.csv", ("schema_name", "object_name", "index_name", "column_ordinal"), ("column_name", "key_ordinal", "is_included_column", "is_unique", "filter_definition", "is_disabled")),
    "constraints": CatalogueSpec("07_Indexes_Constraints/CONSTRAINT_CATALOGUE.csv", ("schema_name", "object_name", "constraint_name", "column_name"), ("constraint_type", "definition", "is_disabled", "is_not_trusted")),
    "views": CatalogueSpec("08_Views/VIEW_CATALOGUE.csv", ("schema_name", "object_name"), ("definition_sha256",), (), "definition_sanitized"),
    "procedures": CatalogueSpec("09_Stored_Procedures/STORED_PROCEDURE_CATALOGUE.csv", ("schema_name", "object_name"), ("definition_sha256",), (), "definition_sanitized"),
    "functions": CatalogueSpec("10_Functions/FUNCTION_CATALOGUE.csv", ("schema_name", "object_name"), ("definition_sha256",), (), "definition_sanitized"),
    "triggers": CatalogueSpec("11_Triggers/TRIGGER_CATALOGUE.csv", ("parent_schema_name", "object_name"), ("definition_sha256", "is_disabled"), (), "definition_sanitized"),
    "synonyms": CatalogueSpec("12_Synonyms_Sequences/SYNONYM_CATALOGUE.csv", ("schema_name", "object_name"), ("base_object_name",)),
    "sequences": CatalogueSpec("12_Synonyms_Sequences/SEQUENCE_CATALOGUE.csv", ("schema_name", "object_name"), ("data_type", "start_value", "increment_value", "minimum_value", "maximum_value", "is_cycling")),
    "row_counts": CatalogueSpec("04_Tables/TABLE_SIZE_PROFILE.csv", ("schema_name", "object_name"), ("row_count", "row_count_type"), ("row_count",)),
    "table_sizes": CatalogueSpec("04_Tables/TABLE_SIZE_PROFILE.csv", ("schema_name", "object_name"), ("reserved_kb", "used_kb", "data_kb", "index_kb"), ("reserved_kb", "used_kb", "data_kb", "index_kb")),
    "table_shapes": CatalogueSpec("04_Tables/TABLE_SHAPE_PROFILE.csv", ("schema_name", "object_name"), ("row_count", "column_count", "nullable_columns", "identity_columns", "computed_columns"), ("row_count", "column_count", "nullable_columns", "identity_columns", "computed_columns")),
    "column_profiles": CatalogueSpec("13_Data_Profiling/COLUMN_PROFILE.csv", ("schema_name", "object_name", "column_name"), ("null_percent", "distinct_count", "minimum_value", "maximum_value", "profile_status"), ("null_percent", "distinct_count")),
    "dependencies": CatalogueSpec("15_Lineage/OBJECT_DEPENDENCIES.csv", ("source_schema", "source_object", "target_database", "target_schema", "target_object", "target_column"), ("source_type", "operation", "evidence")),
    "lineage": CatalogueSpec("15_Lineage/LINEAGE_EDGES.csv", ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column"), ("relationship", "lineage_type", "confidence")),
    "pipelines": CatalogueSpec("16_Pipelines/PIPELINE_CATALOGUE.csv", ("origin", "source", "destination"), ("transformation", "schedule", "classification", "confidence")),
    "risks": CatalogueSpec("18_Risks_Uncertainties/RISK_AND_UNCERTAINTY_REGISTER.csv", ("category", "object_context", "observation"), ("severity", "evidence_type", "uncertainty")),
    "errors": CatalogueSpec("00_Run_Metadata/DISCOVERY_ERRORS.csv", ("prompt", "stage", "schema_name", "object_name", "query_name"), ("error_type", "impact", "continuation")),
    "sql_agent_jobs": CatalogueSpec("16_Pipelines/SQL_AGENT_JOB_CATALOGUE.csv", ("job_name", "step_id"), ("step_name", "subsystem", "database_name", "command_sha256", "schedule_name", "is_enabled")),
    "database_files": CatalogueSpec("02_Server_Database/DATABASE_FILES.csv", ("file_id",), ("file_name", "file_type", "filegroup_name", "state_desc", "size_kb", "max_size_kb", "growth", "is_percent_growth", "is_read_only"), ("size_kb", "max_size_kb", "growth")),
    "filegroups": CatalogueSpec("02_Server_Database/FILEGROUP_CATALOGUE.csv", ("data_space_id",), ("filegroup_name", "type_desc", "is_default", "is_read_only", "file_count", "total_size_kb"), ("file_count", "total_size_kb")),
    "partition_functions": CatalogueSpec("07_Indexes_Constraints/PARTITION_FUNCTIONS.csv", ("function_name", "parameter_id"), ("type_desc", "boundary_value_on_right", "fanout", "type_schema_name", "data_type", "max_length", "precision", "scale"), ("fanout",)),
    "partition_schemes": CatalogueSpec("07_Indexes_Constraints/PARTITION_SCHEMES.csv", ("scheme_name", "destination_id"), ("function_name", "destination_data_space_id", "filegroup_name")),
    "partition_compression": CatalogueSpec("04_Tables/PARTITION_COMPRESSION.csv", ("schema_name", "object_name", "index_id", "partition_number"), ("index_name", "row_count", "data_compression", "data_space_name"), ("row_count",)),
    "user_defined_types": CatalogueSpec("05_Columns/USER_DEFINED_TYPES.csv", ("type_schema_name", "type_name"), ("system_type_name", "max_length", "precision", "scale", "collation_name", "is_nullable", "is_table_type", "is_assembly_type"), ("max_length", "precision", "scale")),
    "statistics": CatalogueSpec("07_Indexes_Constraints/STATISTICS_CATALOGUE.csv", ("schema_name", "object_name", "statistics_name", "stats_column_id"), ("auto_created", "user_created", "no_recompute", "has_filter", "filter_definition", "column_id", "column_name")),
    "fulltext_catalogs": CatalogueSpec("07_Indexes_Constraints/FULLTEXT_CATALOGUES.csv", ("fulltext_catalog_id",), ("catalog_name", "is_default", "is_accent_sensitivity_on", "is_importing")),
    "fulltext_indexes": CatalogueSpec("07_Indexes_Constraints/FULLTEXT_INDEXES.csv", ("schema_name", "object_name"), ("unique_index_name", "catalog_name", "is_enabled", "change_tracking_state", "has_crawl_completed", "crawl_type")),
    "cdc_status": CatalogueSpec("02_Server_Database/CDC_STATUS.csv", ("scope", "schema_name", "object_name"), ("is_cdc_enabled", "is_tracked_by_cdc")),
    "change_tracking_status": CatalogueSpec("02_Server_Database/CHANGE_TRACKING_STATUS.csv", ("scope", "schema_name", "object_name"), ("is_auto_cleanup_on", "retention_period", "retention_period_units", "is_track_columns_updated_on", "begin_version", "cleanup_version", "min_valid_version"), ("retention_period", "begin_version", "cleanup_version", "min_valid_version")),
    "database_scoped_configurations": CatalogueSpec("02_Server_Database/DATABASE_SCOPED_CONFIGURATIONS.csv", ("configuration_id",), ("configuration_name", "configured_value", "value_for_secondary")),
    "xml_schema_collections": CatalogueSpec("05_Columns/XML_SCHEMA_COLLECTIONS.csv", ("xml_collection_id",), ("schema_name", "collection_name", "principal_id", "modify_date")),
    "security_principals": CatalogueSpec("02_Server_Database/SECURITY_PRINCIPALS.csv", ("principal_id",), ("principal_type", "authentication_type", "principal_name_sha256", "default_schema_name", "modify_date", "is_fixed_role")),
    "mssql_feature_support": CatalogueSpec("02_Server_Database/MSSQL_FEATURE_SUPPORT_OVERVIEW.csv", ("query_name",), ("feature_family", "status", "row_count", "evidence"), ("row_count",)),
}


def summarize_rows(rows: list[dict[str, Any]], *, scope: str, category: str | None = None) -> dict[str, Any]:
    """Return explicit, arithmetically checkable row and event totals."""
    primary = Counter(str(row.get("status") or "UNKNOWN") for row in rows)
    intervals = Counter(
        str(status)
        for row in rows
        for status in (row.get("intervals") or {}).values()
    )
    events = Counter(
        str(event)
        for row in rows
        for event in (row.get("timeline_events") or ())
    )
    result: dict[str, Any] = {
        "scope": scope,
        "row_count": len(rows),
        "primary_status_counts": dict(sorted(primary.items())),
        "interval_status_occurrences": dict(sorted(intervals.items())),
        "timeline_event_occurrences": dict(sorted(events.items())),
        "counting_note": "Primary status counts sum to row_count. Interval and timeline counts are event occurrences and may exceed row_count.",
    }
    if category is not None:
        result["category"] = category
    return result


def _text_record(snapshot: RunSnapshot, path: str) -> list[dict[str, Any]]:
    text = snapshot.text(path)
    if text is None: return []
    return [{"document": path, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "text": text}]


def _flatten_metrics(value: Any, prefix: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in sorted(value.items()):
            name = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_metrics(item, name))
    elif isinstance(value, (str, int, float, bool)) or value is None:
        rows.append({"metric": prefix, "value": value})
    return rows


def _type_records(snapshot: RunSnapshot) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("data_type") or "UNKNOWN") for row in snapshot.csv("05_Columns/COLUMN_CATALOGUE.csv"))
    return [{"data_type": name, "column_count": count} for name, count in sorted(counts.items())]


def _definition_records(snapshot: RunSnapshot) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for object_type, path, schema_field in (
        ("VIEW", "08_Views/VIEW_CATALOGUE.csv", "schema_name"),
        ("PROCEDURE", "09_Stored_Procedures/STORED_PROCEDURE_CATALOGUE.csv", "schema_name"),
        ("FUNCTION", "10_Functions/FUNCTION_CATALOGUE.csv", "schema_name"),
        ("TRIGGER", "11_Triggers/TRIGGER_CATALOGUE.csv", "parent_schema_name"),
    ):
        for row in snapshot.csv(path):
            rows.append({"object_type": object_type, "schema_name": row.get(schema_field, ""), "object_name": row.get("object_name", ""), "definition_sha256": row.get("definition_sha256", ""), "definition_sanitized": row.get("definition_sanitized", "")})
    return rows


def _availability_status(availability: dict[str, bool]) -> str:
    if all(availability.values()): return "AVAILABLE"
    if any(availability.values()): return "NOT_COMPARABLE"
    return "NOT_AVAILABLE"


def compare_run_paths(runs: list[RunSnapshot | str]) -> dict[str, Any]:
    snapshots = [item if isinstance(item, RunSnapshot) else load_run(item) for item in runs]
    if len(snapshots) not in {2, 3}: raise ValueError("Select exactly two or three runs")
    labels = ["A", "B", "C"][:len(snapshots)]
    run_meta = {label: {**snapshot.summary, "label": snapshot.label, "path": str(snapshot.root), "origin": snapshot.origin} for label, snapshot in zip(labels, snapshots, strict=True)}
    warnings = []
    if len({snapshot.database.casefold() for snapshot in snapshots}) > 1: warnings.append("Mixed databases: matching structural names do not prove business equivalence.")
    if len({str(snapshot.summary.get('mode')) for snapshot in snapshots}) > 1: warnings.append("Discovery modes differ; unavailable evidence may not be comparable.")
    categories: dict[str, Any] = {}
    for name, spec in CATALOGUES.items():
        rows = {label: snapshot.csv(spec.path) for label, snapshot in zip(labels, snapshots, strict=True)}
        availability = {label: snapshot.exists(spec.path) for label, snapshot in zip(labels, snapshots, strict=True)}
        compared = compare_rows(rows, spec.keys, spec.fields, spec.numeric, spec.definition, availability)
        categories[name] = {"path": spec.path, "rows": compared, "count": len(compared), "availability": availability, "status": _availability_status(availability)}
    summary_path = "02_Server_Database/DATABASE_SUMMARY_METRICS.json"
    summary_availability = {label: snapshot.exists(summary_path) for label, snapshot in zip(labels, snapshots, strict=True)}
    summary_rows = {label: _flatten_metrics(snapshot.json(summary_path) or {}) for label, snapshot in zip(labels, snapshots, strict=True)}
    summary_compared = compare_rows(summary_rows, ("metric",), ("value",), ("value",), availability=summary_availability)
    categories["database_summary"] = {"path": summary_path, "rows": summary_compared, "count": len(summary_compared), "availability": summary_availability, "status": _availability_status(summary_availability)}

    types_path = "05_Columns/COLUMN_CATALOGUE.csv"
    types_availability = {label: snapshot.exists(types_path) for label, snapshot in zip(labels, snapshots, strict=True)}
    type_rows = {label: _type_records(snapshot) for label, snapshot in zip(labels, snapshots, strict=True)}
    types_compared = compare_rows(type_rows, ("data_type",), ("column_count",), ("column_count",), availability=types_availability)
    categories["data_types"] = {"path": types_path, "rows": types_compared, "count": len(types_compared), "availability": types_availability, "status": _availability_status(types_availability)}

    definition_paths = ("08_Views/VIEW_CATALOGUE.csv", "09_Stored_Procedures/STORED_PROCEDURE_CATALOGUE.csv", "10_Functions/FUNCTION_CATALOGUE.csv", "11_Triggers/TRIGGER_CATALOGUE.csv")
    definition_availability = {label: any(snapshot.exists(path) for path in definition_paths) for label, snapshot in zip(labels, snapshots, strict=True)}
    definition_rows = {label: _definition_records(snapshot) for label, snapshot in zip(labels, snapshots, strict=True)}
    definition_compared = compare_rows(definition_rows, ("object_type", "schema_name", "object_name"), ("definition_sha256",), definition_field="definition_sanitized", availability=definition_availability)
    categories["definition_hashes"] = {"path": "programmable object catalogues", "rows": definition_compared, "count": len(definition_compared), "availability": definition_availability, "status": _availability_status(definition_availability)}

    for name, path in {"data_quality": "17_Data_Quality/DATA_QUALITY_SUMMARY.md", "coverage": "00_Run_Metadata/DISCOVERY_COVERAGE.md"}.items():
        rows = {label: _text_record(snapshot, path) for label, snapshot in zip(labels, snapshots, strict=True)}
        availability = {label: snapshot.exists(path) for label, snapshot in zip(labels, snapshots, strict=True)}
        compared = compare_rows(rows, ("document",), ("sha256",), definition_field="text", availability=availability)
        categories[name] = {"path": path, "rows": compared, "count": len(compared), "availability": availability, "status": _availability_status(availability)}
    for payload in categories.values():
        for row in payload["rows"]:
            row["databases"] = [
                snapshot.database
                for label, snapshot in zip(labels, snapshots, strict=True)
                if row.get("runs", {}).get(label) is not None
            ]
    all_rows: list[dict[str, Any]] = []
    for name, payload in categories.items():
        payload["summary"] = summarize_rows(payload["rows"], scope="CATEGORY_ALL_ROWS", category=name)
        all_rows.extend(payload["rows"])
    summary = summarize_rows(all_rows, scope="GLOBAL_ALL_CATEGORY_ROWS")
    summary["category_count"] = len(categories)
    summary["category_row_counts"] = {name: payload["count"] for name, payload in categories.items()}
    summary["scope_note"] = "Every displayed/exported category row is counted once. Analytical categories may intentionally describe overlapping source evidence."
    return {"schema_version": 4, "runs": run_meta, "warnings": warnings, "semantic_note": "Structural evidence only. The comparison does not infer cause, business equivalence, or runtime behavior.", "summary": summary, "categories": categories}
