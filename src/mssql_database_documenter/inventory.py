"""Metadata-only inventory runner with isolated, reproducible output."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
from typing import Iterable

from . import __version__
from .config import Settings
from .metadata.support import FEATURE_SUPPORT_HEADERS, feature_support_markdown, is_unsupported_metadata_error, support_record
from .mode_policy import resolve_mode_policy
from .connection import connect
from .queries import METADATA_QUERIES, SECURITY_METADATA_QUERIES, QuerySpec
from .redaction import redact_text
from .safety import ReadOnlyCursor, validate_read_only_sql


OUTPUT_FOLDERS = (
    "00_Run_Metadata", "01_Executive_Summary", "02_Server_Database", "03_Schemas",
    "04_Tables", "05_Columns", "06_Keys_Relationships", "07_Indexes_Constraints",
    "08_Views", "09_Stored_Procedures", "10_Functions", "11_Triggers",
    "12_Synonyms_Sequences", "13_Data_Profiling", "14_Samples", "15_Lineage",
    "16_Pipelines", "17_Data_Quality", "18_Risks_Uncertainties", "19_Diagrams",
    "20_Object_Documentation", "21_HTML_Report", "99_Git_Handoff",
)


@dataclass(frozen=True, slots=True)
class InventoryResult:
    database: str
    run_directory: Path
    query_count: int
    error_count: int
    row_counts: dict[str, int]


def safe_path_component(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._ -]+", "_", value).strip(" .")
    return (clean or "unnamed_database")[:100]


def _new_run_directory(output_root: Path, database: str) -> tuple[str, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = output_root / safe_path_component(database)
    candidate = base / f"run_{timestamp}"
    suffix = 1
    while candidate.exists():
        candidate = base / f"run_{timestamp}_{suffix:02d}"
        suffix += 1
    # Reserve only the truthful run root. Evidence subfolders are created by
    # their writers when and only when the corresponding stage produces them.
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate.name.removeprefix("run_"), candidate


def _write_csv(path: Path, columns: Iterable[str], rows: list[dict[str, object]]) -> None:
    headers = list(columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _fetch(cursor: ReadOnlyCursor, query: QuerySpec) -> list[dict[str, object]]:
    validate_read_only_sql(query.sql)
    cursor.execute(query.sql)
    actual_columns = tuple(item[0] for item in cursor.description)
    if query.columns and tuple(name.casefold() for name in actual_columns) != tuple(name.casefold() for name in query.columns):
        raise RuntimeError(
            f"Query {query.name} returned an unexpected schema: {actual_columns!r}"
        )
    return [dict(zip(actual_columns, row, strict=True)) for row in cursor.fetchall()]


def _write_narratives(
    run_directory: Path,
    database: str,
    row_counts: dict[str, int],
    errors: list[dict[str, object]],
    attempted_query_count: int,
) -> None:
    (run_directory / "02_Server_Database").mkdir(parents=True, exist_ok=True)
    (run_directory / "00_Run_Metadata").mkdir(parents=True, exist_ok=True)
    metrics = {
        "database": database,
        "stage": "metadata",
        "catalogue_row_counts": row_counts,
        "query_count": attempted_query_count,
        "successful_query_count": attempted_query_count - len(errors),
        "error_count": len(errors),
    }
    (run_directory / "02_Server_Database" / "DATABASE_SUMMARY_METRICS.json").write_text(
        json.dumps(metrics, indent=2, default=str) + "\n", encoding="utf-8"
    )
    overview_lines = [
        f"# Database Overview — {database}", "", "Evidence classification: FACT from SQL Server catalog queries.", "",
        "This run contains the metadata-only stage. Programmable-object logic, profiling, samples, inferred relationships, lineage, and pipelines have not run yet.", "",
        "## Catalogue row counts", "",
    ]
    overview_lines.extend(f"- `{name}`: {count}" for name, count in sorted(row_counts.items()))
    (run_directory / "02_Server_Database" / "DATABASE_OVERVIEW.md").write_text(
        "\n".join(overview_lines) + "\n", encoding="utf-8"
    )
    coverage_lines = [
        "# Discovery Coverage", "", "## Completed", "",
        f"- Metadata queries attempted: {attempted_query_count}",
        f"- Metadata queries successful: {attempted_query_count - len(errors)}",
        f"- Metadata queries with errors: {len(errors)}", "", "## Not yet run", "",
        "- Static programmable-object analysis", "- Data profiling and samples",
        "- Inferred relationships, cardinality, and orphan validation", "- Lineage and pipeline analysis",
        "- Data-quality and final risk synthesis", "",
        "Absence from this staged run is not evidence that an object category is absent from the database.",
    ]
    (run_directory / "00_Run_Metadata" / "DISCOVERY_COVERAGE.md").write_text(
        "\n".join(coverage_lines) + "\n", encoding="utf-8"
    )


def _write_manifest_and_checksums(
    run_directory: Path,
    run_id: str,
    database: str,
    settings: Settings,
    errors: list[dict[str, object]],
) -> None:
    policy = resolve_mode_policy(settings, "metadata")
    configuration = {
        **settings.sanitized(),
        "requested_discovery_mode": settings.discovery_mode,
        "discovery_mode": "metadata",
        "resolved_mode_policy": policy.as_dict(),
    }
    (run_directory / "00_Run_Metadata").mkdir(parents=True, exist_ok=True)
    manifest_path = run_directory / "00_Run_Metadata" / "manifest.json"
    checksum_path = run_directory / "00_Run_Metadata" / "checksums.sha256"
    summary_path = run_directory / "00_Run_Metadata" / "run_summary.json"
    summary_path.write_text(json.dumps({
        "run_id": run_id, "database": database, "server_alias": settings.sanitized()["server"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": "metadata",
        "status": "COMPLETED_WITH_WARNINGS" if errors else "COMPLETED", "tool_version": __version__,
        "sql_server_version": "UNKNOWN",
        "sample_rows": policy.sample_row_limit, "exact_row_counts": policy.exact_counts,
        "mask_sensitive_data": settings.profile_mask_sensitive_data,
        "profile_settings": {"sample_rows": policy.sample_row_limit, "include_sample_data": policy.samples, "sample_tables": policy.sample_tables, "sample_views": policy.sample_views, "sample_large_tables": policy.sample_large_tables, "mask_sensitive_data": settings.profile_mask_sensitive_data, "exact_row_counts": policy.exact_counts, "exact_row_count_threshold": policy.exact_count_ceiling, "large_table_threshold": policy.profile_row_threshold},
        "resolved_mode_policy": policy.as_dict(),
        "completed_stage_count": 2,
        "completion_coverage": "2/2",
        "error_count": 0, "warning_count": len(errors),
        "warning_error_count": len(errors),
    }, indent=2, default=str) + "\n", encoding="utf-8")
    existing = sorted(
        path.relative_to(run_directory).as_posix()
        for path in run_directory.rglob("*")
        if path.is_file()
    )
    files = sorted(set(existing + [
        manifest_path.relative_to(run_directory).as_posix(),
        checksum_path.relative_to(run_directory).as_posix(),
        summary_path.relative_to(run_directory).as_posix(),
    ]))
    manifest = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tool": "mssql-database-documenter",
        "tool_version": __version__,
        "python_version": platform.python_version(),
        "configuration": configuration,
        "resolved_mode_policy": policy.as_dict(),
        "database": database,
        "completed_stages": ["connection", "metadata"],
        "warnings": [str(item["sanitized_message"]) for item in errors],
        "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    lines = []
    for path in sorted(path for path in run_directory.rglob("*") if path.is_file() and path != checksum_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(run_directory).as_posix()}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_inventory(settings: Settings, database: str) -> InventoryResult:
    settings.validate_for_connection()
    run_id, run_directory = _new_run_directory(settings.output_root, database)
    row_counts: dict[str, int] = {}
    errors: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    sensitive_values = (settings.password, settings.username, settings.server)
    attempted_queries = list(METADATA_QUERIES)
    if settings.discover_security_metadata:
        attempted_queries.extend(SECURITY_METADATA_QUERIES)
    else:
        for query in SECURITY_METADATA_QUERIES:
            _write_csv(run_directory / query.output_folder / query.output_name, query.columns, [])
            support_rows.append(support_record(query, row_count=0, state="DISABLED"))

    with connect(settings, database) as connection:
        cursor = ReadOnlyCursor(connection.cursor())
        for query in attempted_queries:
            output_path = run_directory / query.output_folder / query.output_name
            try:
                rows = _fetch(cursor, query)
                row_counts[query.name] = len(rows)
                _write_csv(output_path, query.columns, rows)
                if query.feature_family:
                    support_rows.append(support_record(query, row_count=len(rows)))
            except Exception as exc:
                row_counts[query.name] = 0
                errors.append({
                    "stage": query.stage,
                    "database": database,
                    "schema_name": "",
                    "object_name": "",
                    "query_name": query.name,
                    "error_type": type(exc).__name__,
                    "sanitized_message": redact_text(exc, sensitive_values=sensitive_values),
                    "impact": f"{query.output_name} contains headers only",
                    "continuation": "Independent metadata queries continued",
                })
                _write_csv(output_path, query.columns, [])
                if query.feature_family:
                    state = "UNSUPPORTED" if is_unsupported_metadata_error(exc) else "INACCESSIBLE"
                    support_rows.append(support_record(query, row_count=0, state=state))

    error_columns = (
        "stage", "database", "schema_name", "object_name", "query_name", "error_type",
        "sanitized_message", "impact", "continuation",
    )
    _write_csv(run_directory / "00_Run_Metadata" / "DISCOVERY_ERRORS.csv", error_columns, errors)
    _write_csv(run_directory / "02_Server_Database" / "MSSQL_FEATURE_SUPPORT_OVERVIEW.csv", FEATURE_SUPPORT_HEADERS, support_rows)
    (run_directory / "02_Server_Database" / "MSSQL_FEATURE_SUPPORT_OVERVIEW.md").write_text(
        feature_support_markdown(support_rows), encoding="utf-8"
    )
    _write_narratives(run_directory, database, row_counts, errors, len(attempted_queries))
    (run_directory / "00_Run_Metadata" / "RUN_CONFIGURATION.json").write_text(
        json.dumps(settings.sanitized(), indent=2) + "\n", encoding="utf-8"
    )
    _write_manifest_and_checksums(run_directory, run_id, database, settings, errors)
    return InventoryResult(database, run_directory, len(attempted_queries), len(errors), row_counts)
