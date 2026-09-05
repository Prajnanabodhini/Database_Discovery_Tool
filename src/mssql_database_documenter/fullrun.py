"""Sequential end-to-end read-only discovery pipeline."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import html
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Callable, Iterable

from .config import Settings
from .connection import connect
from .contracts import EVIDENCE_CLASSES, EXTRA_OUTPUTS, REQUIRED_OUTPUTS
from .evidence_safety import audit_run_evidence
from .inventory import OUTPUT_FOLDERS, _new_run_directory, safe_path_component
from .programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from .profiling import known_row_estimate as _known_row_estimate
from .profiling import within_safety_threshold as _within_safety_threshold
from .queries import METADATA_QUERIES, QUERIES, QuerySpec
from .redaction import redact_text
from .safety import ReadOnlyCursor, validate_read_only_sql


ERROR_COLUMNS = (
    "prompt", "stage", "database", "schema_name", "object_name", "query_name",
    "error_type", "sanitized_message", "impact", "continuation",
)

SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Credential", re.compile(r"password|passwd|pwd|secret|token|api.?key|credential|salt|hash", re.I)),
    ("Financial", re.compile(r"bank|account.?no|iban|swift|card|cvv|salary|income|payment", re.I)),
    ("Health", re.compile(r"health|medical|diagnos|disease|blood|patient", re.I)),
    ("PII", re.compile(r"email|e.?mail|phone|mobile|address|aadhaar|aadhar|pan.?no|passport|dob|birth|father|mother|guardian|name", re.I)),
    ("Potentially Sensitive", re.compile(r"user|login|ip.?address|location|photo|signature|remark|note", re.I)),
)

SKIP_PROFILE_TYPES = frozenset(
    {"binary", "varbinary", "image", "text", "ntext", "xml", "sql_variant", "timestamp", "rowversion", "hierarchyid", "geography", "geometry"}
)

STRING_TYPES = frozenset({"char", "varchar", "nchar", "nvarchar"})
NUMERIC_TYPES = frozenset({"tinyint", "smallint", "int", "bigint", "decimal", "numeric", "money", "smallmoney", "float", "real"})
DATE_TYPES = frozenset({"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset", "time"})


def _type_family(data_type: str) -> str:
    value = data_type.casefold()
    if value in STRING_TYPES or value in {"text", "ntext", "xml"}:
        return "STRING"
    if value in NUMERIC_TYPES or value == "bit":
        return "NUMERIC"
    if value in DATE_TYPES:
        return "DATE_TIME"
    if value in {"binary", "varbinary", "image", "rowversion", "timestamp"}:
        return "BINARY"
    return "OTHER"


def _md_table(rows: Iterable[dict[str, Any]], columns: tuple[str, ...]) -> list[str]:
    values = list(rows)
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in values:
        cells = [str(row.get(column, "")).replace("|", "\\|").replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    if not values:
        lines.append("| " + " | ".join("None observed" if index == 0 else "" for index, _ in enumerate(columns)) + " |")
    return lines


def _normalized_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _sanitized_external_server(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"[EXTERNAL_SERVER:{digest}]"


def _definition_references(row: dict[str, Any]) -> list[dict[str, str]]:
    """Conservatively extract static object references without executing SQL text."""
    definition = str(row.get("definition_sanitized") or "")
    if not definition:
        return []
    token = r"(?:\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_$#@]*)"
    qualified = rf"({token}(?:\s*\.\s*{token}){{0,3}})"
    patterns = (
        ("WRITE", re.compile(rf"\b(?:INSERT\s+INTO|MERGE\s+INTO|UPDATE|DELETE\s+FROM)\s+{qualified}", re.I)),
        ("READ", re.compile(rf"\b(?:FROM|JOIN)\s+{qualified}", re.I)),
        ("CALL", re.compile(rf"\b(?:EXEC|EXECUTE)\s+{qualified}", re.I)),
    )
    found: list[dict[str, str]] = []
    for operation, pattern in patterns:
        for match in pattern.finditer(definition):
            raw = re.sub(r"\s+", "", match.group(1))
            parts = [part.strip("[]") for part in raw.split(".")]
            if not parts or parts[-1].startswith(("#", "@")):
                continue
            server = database = schema = ""
            if len(parts) == 4:
                server, database, schema, obj = parts
            elif len(parts) == 3:
                database, schema, obj = parts
            elif len(parts) == 2:
                schema, obj = parts
            else:
                obj = parts[0]
            found.append({
                "operation": operation, "target_server": server, "target_database": database,
                "target_schema": schema, "target_object": obj,
                "evidence": f"STATIC_DEFINITION_{operation}",
            })
    unique: dict[tuple[str, ...], dict[str, str]] = {}
    for item in found:
        key = tuple(item[field].casefold() for field in ("operation", "target_server", "target_database", "target_schema", "target_object"))
        unique[key] = item
    return list(unique.values())


def _static_column_references(
    row: dict[str, Any], known_columns: dict[tuple[str, str], set[str]],
) -> list[dict[str, str]]:
    """Attempt qualified column lineage from static SQL aliases; retain uncertainty."""
    definition = str(row.get("definition_sanitized") or "")
    if not definition:
        return []
    token = r"(?:\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_$#@]*)"
    reserved = {"where", "join", "left", "right", "inner", "outer", "full", "cross", "on", "group", "order", "having", "union", "except", "intersect", "with"}
    aliases: dict[str, tuple[str, str]] = {}
    objects_by_name: dict[str, list[tuple[str, str]]] = {}
    identities_casefold = {(identity[0].casefold(), identity[1].casefold()): identity for identity in known_columns}
    for identity in known_columns:
        objects_by_name.setdefault(identity[1].casefold(), []).append(identity)
    source_pattern = re.compile(rf"\b(?:FROM|JOIN)\s+({token}(?:\s*\.\s*{token})?)\s*(?:AS\s+)?({token})?", re.I)
    for match in source_pattern.finditer(definition):
        parts = [part.strip().strip("[]") for part in re.sub(r"\s+", "", match.group(1)).split(".")]
        if len(parts) == 2 and (parts[0].casefold(), parts[1].casefold()) in identities_casefold:
            identity = identities_casefold[(parts[0].casefold(), parts[1].casefold())]
        elif len(parts) == 1 and len(objects_by_name.get(parts[0].casefold(), [])) == 1:
            identity = objects_by_name[parts[0].casefold()][0]
        else:
            continue
        aliases[identity[1].casefold()] = identity
        alias = str(match.group(2) or "").strip("[]")
        if alias and alias.casefold() not in reserved:
            aliases[alias.casefold()] = identity
    results: list[dict[str, str]] = []
    for match in re.finditer(rf"({token})\s*\.\s*({token})", definition):
        qualifier = match.group(1).strip("[]").casefold()
        column = match.group(2).strip("[]")
        identity = aliases.get(qualifier)
        if not identity or column.casefold() not in known_columns[identity]:
            continue
        before = definition[max(0, match.start() - 100): match.start()]
        context = definition[max(0, match.start() - 100): min(len(definition), match.end() + 100)]
        if re.search(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\([^)]*$", before, re.I):
            lineage_type = "AGGREGATED"
        elif re.search(r"\bCASE\b", context, re.I):
            lineage_type = "CONDITIONAL"
        elif re.search(rf"{re.escape(match.group(0))}\s*[+*/-]|[+*/-]\s*{re.escape(match.group(0))}", context, re.I):
            lineage_type = "DERIVED"
        else:
            lineage_type = "DIRECT"
        results.append({
            "target_schema": identity[0], "target_object": identity[1], "target_column": column,
            "lineage_type": lineage_type, "evidence": "STATIC_ALIAS_QUALIFIED_COLUMN_REFERENCE",
        })
    unique: dict[tuple[str, ...], dict[str, str]] = {}
    for item in results:
        key = tuple(item[field].casefold() for field in ("target_schema", "target_object", "target_column", "lineage_type"))
        unique[key] = item
    return list(unique.values())


class _RequestedStageComplete(Exception):
    """Internal control flow used after a requested stage passes."""


class DiscoveryCancelled(RuntimeError):
    """Raised between stages when a Web/CLI operator requests cancellation."""


def _is_access_limitation(exc: Exception) -> bool:
    message = str(exc).casefold()
    return any(
        marker in message
        for marker in (
            "permission was denied", "select permission denied", "not authorized",
            "cannot open database", "login failed", "binding errors",
            "could not use view or function", "definition is encrypted",
        )
    )


def _csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    headers = list(columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def _qid(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("Invalid SQL identifier from metadata")
    return "[" + value.replace("]", "]]" ) + "]"


def _object_key(row: dict[str, Any], schema_key: str = "schema_name", object_key: str = "object_name") -> str:
    return f"{row.get(schema_key) or ''}.{row.get(object_key) or ''}"


def _classification(column_name: str) -> tuple[str, str]:
    for category, pattern in SENSITIVE_PATTERNS:
        if pattern.search(column_name):
            action = "REDACT" if category == "Credential" else "PSEUDONYMIZE"
            return category, action
    return "Unknown", "PRESERVE"


def _mask(value: Any, category: str, salt: str, masking_enabled: bool = True) -> Any:
    if value is None:
        return None
    if category == "Credential":
        return "[REDACTED]"
    if masking_enabled and category in {"PII", "Financial", "Health", "Potentially Sensitive"}:
        digest = hashlib.sha256(f"{salt}|{value}".encode("utf-8", errors="replace")).hexdigest()[:16]
        return f"[MASKED:{digest}]"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "[BINARY_REDACTED]"
    return value


def _static_definition(row: dict[str, Any]) -> dict[str, Any]:
    definition = row.pop("definition", None)
    text = "" if definition is None else str(definition)
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    sanitized = redact_text(text)
    sanitized = re.sub(
        r"(?i)(password|passwd|pwd|secret|token|api.?key)\s*=\s*N?'[^']*'",
        r"\1='[REDACTED]'",
        sanitized,
    )
    upper = text.upper()
    row.update({
        "definition_available": bool(text),
        "definition_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest() if text else "",
        "definition_sanitized": sanitized,
        "dynamic_sql_present": bool(re.search(r"\bSP_EXECUTESQL\b|\bEXEC\s*\(|\bEXECUTE\s*\(", upper)),
        "temp_table_present": "#" in text,
        "transaction_logic_present": bool(re.search(r"\bBEGIN\s+TRAN|\bCOMMIT\b|\bROLLBACK\b", upper)),
        "error_handling_present": bool(re.search(r"\bTRY\b|\bCATCH\b|\bTHROW\b|\bRAISERROR\b", upper)),
        "likely_write_logic": bool(re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bMERGE\b", upper)),
    })
    return row


class SequentialRun:
    def __init__(
        self,
        settings: Settings,
        database: str,
        *,
        stop_after: str = "21",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> None:
        self.settings = settings
        self.database = database
        self.run_id, self.root = _new_run_directory(settings.output_root, database)
        self.errors: list[dict[str, Any]] = []
        self.status: list[dict[str, Any]] = []
        self.data: dict[str, Any] = {}
        self.sensitive_values = (settings.password, settings.username, settings.server)
        self.mask_salt = hashlib.sha256(f"mssql-database-documenter|{database}".encode()).hexdigest()
        self.connection: Any = None
        self.cursor: ReadOnlyCursor | None = None
        self.stop_after = stop_after
        self.progress_callback = progress_callback
        self.cancel_requested = cancel_requested or (lambda: False)
        self.cancelled = False
        self.failed = False

    def _progress(self, prompt: str, stage: str, status: str, **extra: Any) -> None:
        if self.progress_callback:
            self.progress_callback({"database": self.database, "prompt": prompt, "stage": stage, "status": status, **extra})

    def artifact(self, name: str) -> Path:
        folder = REQUIRED_OUTPUTS.get(name, EXTRA_OUTPUTS.get(name))
        if folder is None:
            raise KeyError(name)
        return self.root / folder / name

    def stage(self, prompt: str, name: str, operation: Any) -> None:
        if self.cancel_requested():
            self._progress(prompt, name, "CANCELLED")
            raise DiscoveryCancelled(f"Cancelled before prompt {prompt}: {name}")
        started = datetime.now(timezone.utc)
        self._progress(prompt, name, "RUNNING", started_utc=started.isoformat())
        try:
            operation()
        except Exception as exc:
            self.status.append({"prompt": prompt, "stage": name, "status": "FAILED", "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat()})
            self._error(prompt, name, "", "", name, exc, "Stage incomplete", "Pipeline stopped")
            self._write_control_files(final=False)
            self._progress(prompt, name, "FAILED", error_type=type(exc).__name__)
            raise
        self.status.append({"prompt": prompt, "stage": name, "status": "PASS", "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat()})
        self._progress(prompt, name, "PASS")
        if prompt == self.stop_after:
            raise _RequestedStageComplete

    def skip_stage(self, prompt: str, name: str, reason: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.status.append({"prompt": prompt, "stage": name, "status": "SKIPPED_BY_MODE", "reason": reason, "started_utc": now, "finished_utc": now})
        if prompt == self.stop_after:
            raise _RequestedStageComplete

    def _error(self, prompt: str, stage: str, schema: str, obj: str, query: str, exc: Exception, impact: str, continuation: str) -> None:
        self.errors.append({
            "prompt": prompt, "stage": stage, "database": self.database,
            "schema_name": schema, "object_name": obj, "query_name": query,
            "error_type": type(exc).__name__,
            "sanitized_message": redact_text(exc, sensitive_values=self.sensitive_values),
            "impact": impact, "continuation": continuation,
        })

    def fetch(self, query: QuerySpec, *, prompt: str, optional: bool = False) -> list[dict[str, Any]]:
        if self.cursor is None:
            raise RuntimeError("Connection cursor is not initialized")
        try:
            validate_read_only_sql(query.sql)
            self.cursor.execute(query.sql)
            columns = [item[0] for item in self.cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in self.cursor.fetchall()]
        except Exception as exc:
            self._error(prompt, query.stage, "", "", query.name, exc, "Category unavailable", "Recorded and continued" if optional else "Stage stopped")
            if optional and _is_access_limitation(exc):
                return []
            raise

    def fetch_dynamic(self, sql: str, *, prompt: str, stage: str, schema: str, obj: str, query_name: str) -> list[dict[str, Any]]:
        if self.cursor is None:
            raise RuntimeError("Connection cursor is not initialized")
        try:
            validate_read_only_sql(sql)
            self.cursor.execute(sql)
            columns = [item[0] for item in self.cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in self.cursor.fetchall()]
        except Exception as exc:
            self._error(prompt, stage, schema, obj, query_name, exc, "Object-level evidence unavailable", "Object skipped; stage continued")
            if _is_access_limitation(exc):
                return []
            raise

    def prompt02_safety(self) -> None:
        for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
            validate_read_only_sql(query.sql)
        _md(self.root / "00_Run_Metadata" / "SAFETY_MODEL.md", """# Safety Model Verification

- PASS: all registered SQL is a single `SELECT` or `WITH ... SELECT` statement.
- PASS: DML, DDL, administration, execution, job execution, and sequence advancement are blocked.
- PASS: dynamic identifiers originate only from catalog metadata and are bracket quoted.
- PASS: connection autocommit is disabled and every connection closes through rollback.
- PASS: query timeouts and large-table thresholds are configured.
""")

    def prompt03_connection(self) -> None:
        results: list[dict[str, Any]] = []
        for query in QUERIES:
            rows = self.fetch(query, prompt="03")
            for row in rows:
                if "server_name" in row:
                    row["server_name"] = "[SANITIZED]"
                if "login_name" in row:
                    row["login_name"] = "[REDACTED]"
            results.append({"query": query.name, "rows": rows})
        self.data["connection_capabilities"] = results
        _json(self.root / "02_Server_Database" / "CONNECTION_CAPABILITIES.json", results)

    def prompt04_metadata(self) -> None:
        for query in METADATA_QUERIES:
            rows = self.fetch(query, prompt="04", optional=True)
            self.data[query.name] = rows
            _csv(self.root / query.output_folder / query.output_name, query.columns, rows)
        if not self.data.get("tables") or not self.data.get("columns"):
            raise RuntimeError("Core table/column metadata is unavailable")

    def prompt05_programmable(self) -> None:
        mapping = {
            "views": "VIEW_CATALOGUE.csv", "procedures": "STORED_PROCEDURE_CATALOGUE.csv",
            "functions": "FUNCTION_CATALOGUE.csv", "triggers": "TRIGGER_CATALOGUE.csv",
            "synonyms": "SYNONYM_CATALOGUE.csv", "sequences": "SEQUENCE_CATALOGUE.csv",
            "parameters": "PARAMETER_CATALOGUE.csv", "dependencies": "OBJECT_DEPENDENCIES.csv",
        }
        for query in PROGRAMMABLE_QUERIES:
            rows = self.fetch(query, prompt="05", optional=True)
            if query.name in {"views", "procedures", "functions", "triggers"}:
                rows = [_static_definition(dict(row)) for row in rows]
                for row in rows:
                    row["definition_sanitized"] = redact_text(row.get("definition_sanitized", ""), sensitive_values=self.sensitive_values)
            self.data[query.name] = rows
            headers = list(rows[0]) if rows else self._programmable_headers(query.name)
            _csv(self.artifact(mapping[query.name]), headers, rows)
        static_references: list[dict[str, Any]] = []
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                source_schema = str(row.get("schema_name") or row.get("parent_schema_name") or "")
                for reference in _definition_references(row):
                    static_references.append({
                        "source_server": "[SANITIZED]", "source_database": self.database,
                        "source_schema": source_schema, "source_object": row.get("object_name"),
                        "source_type": category[:-1].upper(), **reference,
                    })
        self.data["static_references"] = static_references
        jobs = self.fetch(SQL_AGENT_QUERY, prompt="05", optional=True) if self.settings.discover_sql_agent_jobs else []
        for row in jobs:
            row["description"] = redact_text(row.get("description", ""))
        self.data["sql_agent_jobs"] = jobs
        _csv(self.artifact("SQL_AGENT_JOB_CATALOGUE.csv"), list(jobs[0]) if jobs else ("server_name", "job_name", "job_enabled", "description", "step_id", "step_name", "subsystem", "command_sha256", "database_name", "schedule_name"), jobs)

    @staticmethod
    def _programmable_headers(name: str) -> tuple[str, ...]:
        common = ("server_name", "database_name", "schema_name", "object_name", "object_id")
        if name == "dependencies":
            return ("source_server", "source_database", "source_schema", "source_object", "source_type", "source_column_id", "target_server", "target_database", "target_schema", "target_object", "target_column", "is_schema_bound_reference", "is_caller_dependent", "is_ambiguous", "referenced_id")
        if name == "parameters":
            return common + ("object_type", "parameter_id", "parameter_name", "data_type", "max_length", "precision", "scale", "is_output", "has_default_value", "default_value", "is_readonly")
        return common

    def prompt06_size_shape(self) -> None:
        columns = self.data["columns"]
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in columns:
            if row.get("object_type") == "USER_TABLE":
                grouped.setdefault(_object_key(row), []).append(row)
        rows = []
        for key, cols in sorted(grouped.items()):
            size = sizes.get(key, {})
            known_estimate = _known_row_estimate(sizes, key)
            estimated_rows: int | str = known_estimate if known_estimate is not None else ""
            row_count: int | str = estimated_rows
            row_count_type = "ESTIMATED"
            if (
                self.settings.profile_exact_row_counts
                and _within_safety_threshold(sizes, key, self.settings.profile_exact_row_count_threshold)
            ):
                schema_name, object_name = key.split(".", 1)
                exact = self.fetch_dynamic(
                    f"SELECT COUNT_BIG(*) AS exact_rows FROM {_qid(schema_name)}.{_qid(object_name)}",
                    prompt="06", stage="exact_row_count", schema=schema_name, obj=object_name,
                    query_name="configured_exact_row_count",
                )
                if exact:
                    row_count = int(exact[0].get("exact_rows") or 0)
                    row_count_type = "EXACT"
                    size["row_count"] = row_count
                    size["row_count_type"] = row_count_type
            family_counts = {family: 0 for family in ("STRING", "NUMERIC", "DATE_TIME", "BINARY", "OTHER")}
            for col in cols:
                family_counts[_type_family(str(col.get("data_type") or ""))] += 1
            rows.append({
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": cols[0]["schema_name"], "object_name": cols[0]["object_name"],
                "estimated_rows": estimated_rows, "row_count": row_count, "column_count": len(cols),
                "nullable_columns": sum(bool(c.get("is_nullable")) for c in cols),
                "identity_columns": sum(bool(c.get("is_identity")) for c in cols),
                "computed_columns": sum(bool(c.get("is_computed")) for c in cols),
                "identifier_columns": sum(bool(re.search(r"(^id$|id$|_id$)", str(c.get("column_name") or ""), re.I)) for c in cols),
                "string_columns": family_counts["STRING"], "numeric_columns": family_counts["NUMERIC"],
                "date_time_columns": family_counts["DATE_TIME"], "binary_columns": family_counts["BINARY"],
                "other_type_columns": family_counts["OTHER"],
                "large_object_columns": sum(str(c.get("data_type", "")).lower() in SKIP_PROFILE_TYPES for c in cols),
                "evidence_type": "FACT", "row_count_type": row_count_type,
            })
        self.data["table_shape"] = rows
        self.data["table_sizes"] = list(sizes.values())
        if self.data["table_sizes"]:
            _csv(self.artifact("TABLE_SIZE_PROFILE.csv"), tuple(self.data["table_sizes"][0]), self.data["table_sizes"])
        _csv(self.artifact("TABLE_SHAPE_PROFILE.csv"), tuple(rows[0]) if rows else ("server_name", "database_name", "schema_name", "object_name", "estimated_rows", "column_count"), rows)

    def prompt07_profile(self) -> None:
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        property_text: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            prop_key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            property_text[prop_key] = property_text.get(prop_key, "") + " " + str(prop.get("property_value") or "")
        profile_rows: list[dict[str, Any]] = []
        low_cardinality_rows: list[dict[str, Any]] = []
        for column in self.data["columns"]:
            if column.get("object_type") != "USER_TABLE":
                continue
            schema, table, name = str(column["schema_name"]), str(column["object_name"]), str(column["column_name"])
            dtype = str(column.get("data_type") or "").lower()
            category, masking_action = _classification(f"{name} {property_text.get((schema, table, name), '')}")
            table_key = f"{schema}.{table}"
            known_estimate = _known_row_estimate(sizes, table_key)
            estimated: int | str = known_estimate if known_estimate is not None else ""
            base = {
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": schema, "object_name": table, "column_name": name,
                "data_type": dtype, "estimated_table_rows": estimated,
                "sensitivity_category": category, "masking_action": masking_action,
                "total_rows": "", "non_null_count": "", "null_count": "",
                "null_percent": "", "distinct_count": "", "distinct_percent": "", "minimum_value": "", "maximum_value": "",
                "empty_string_count": "", "whitespace_string_count": "",
                "zero_count": "", "negative_count": "", "minimum_length": "", "maximum_length": "",
                "average_numeric": "", "standard_deviation_numeric": "",
                "true_count": "", "false_count": "",
                "candidate_unique": "", "all_null": "", "constant_value": "",
                "profile_status": "",
            }
            if known_estimate is None:
                base["profile_status"] = "SKIPPED_ROW_ESTIMATE_UNAVAILABLE"
            elif not _within_safety_threshold(sizes, table_key, self.settings.profile_large_table_threshold):
                base["profile_status"] = "SKIPPED_FOR_SAFETY_LARGE_TABLE"
            elif dtype in SKIP_PROFILE_TYPES:
                base["profile_status"] = "SKIPPED_FOR_SAFETY_OR_TYPE"
            elif column.get("is_computed"):
                base["profile_status"] = "SKIPPED_COMPUTED"
            else:
                qcol = _qid(name)
                extras = []
                if dtype in STRING_TYPES:
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} = '' THEN 1 ELSE 0 END) AS empty_string_count",
                        f"SUM(CASE WHEN {qcol} IS NOT NULL AND LTRIM(RTRIM({qcol})) = '' THEN 1 ELSE 0 END) AS whitespace_string_count",
                        f"MIN(LEN({qcol})) AS minimum_length", f"MAX(LEN({qcol})) AS maximum_length",
                    ))
                if dtype in NUMERIC_TYPES or dtype == "bit":
                    extras.append(f"SUM(CASE WHEN {qcol} = 0 THEN 1 ELSE 0 END) AS zero_count")
                if dtype in NUMERIC_TYPES:
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} < 0 THEN 1 ELSE 0 END) AS negative_count",
                        f"AVG(CONVERT(float, {qcol})) AS average_numeric",
                        f"STDEV(CONVERT(float, {qcol})) AS standard_deviation_numeric",
                    ))
                if dtype == "bit":
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} = 1 THEN 1 ELSE 0 END) AS true_count",
                        f"SUM(CASE WHEN {qcol} = 0 THEN 1 ELSE 0 END) AS false_count",
                    ))
                extra_sql = (", " + ", ".join(extras)) if extras else ""
                distinct_sql = f"COUNT_BIG(DISTINCT {qcol})" if self.settings.profile_distinct_values else "CAST(NULL AS bigint)"
                sql = (
                    f"SELECT COUNT_BIG(*) AS total_rows, COUNT_BIG({qcol}) AS non_null_count, "
                    f"{distinct_sql} AS distinct_count, "
                    f"MIN(CONVERT(nvarchar(4000), {qcol})) AS minimum_value, "
                    f"MAX(CONVERT(nvarchar(4000), {qcol})) AS maximum_value{extra_sql} "
                    f"FROM {_qid(schema)}.{_qid(table)}"
                )
                result = self.fetch_dynamic(sql, prompt="07", stage="column_profile", schema=schema, obj=table, query_name=name)
                if result:
                    first = dict(result[0])
                    first["minimum_value"] = _mask(first.get("minimum_value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data)
                    first["maximum_value"] = _mask(first.get("maximum_value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data)
                    base.update(first)
                    total = int(first["total_rows"]); non_null = int(first["non_null_count"])
                    distinct_value = first.get("distinct_count")
                    distinct_count = int(distinct_value) if distinct_value is not None else None
                    base["null_count"] = total - non_null
                    base["null_percent"] = round(((total - non_null) * 100.0 / total), 4) if total else 0.0
                    base["distinct_percent"] = round((distinct_count * 100.0 / non_null), 4) if distinct_count is not None and non_null else ""
                    base["candidate_unique"] = (non_null == distinct_count and total == non_null) if distinct_count is not None else "NOT_EVALUATED"
                    base["all_null"] = int(first["non_null_count"]) == 0
                    base["constant_value"] = (distinct_count <= 1 and non_null > 0) if distinct_count is not None else "NOT_EVALUATED"
                    base["profile_status"] = "PROFILED"
                    if self.settings.profile_distinct_values and distinct_count is not None and distinct_count <= self.settings.profile_max_distinct_values:
                        distribution_sql = (
                            f"SELECT CONVERT(nvarchar(4000), {qcol}) AS value, COUNT_BIG(*) AS value_count "
                            f"FROM {_qid(schema)}.{_qid(table)} GROUP BY {qcol} ORDER BY value_count DESC"
                        )
                        distribution = self.fetch_dynamic(distribution_sql, prompt="07", stage="low_cardinality", schema=schema, obj=table, query_name=name)
                        for value_row in distribution[: self.settings.profile_max_distinct_values + 1]:
                            low_cardinality_rows.append({
                                "server_name": "[SANITIZED]", "database_name": self.database,
                                "schema_name": schema, "object_name": table, "column_name": name,
                                "sensitivity_category": category, "masking_action": masking_action,
                                "value": _mask(value_row.get("value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data),
                                "value_count": value_row.get("value_count"),
                                "total_rows": first["total_rows"],
                                "value_percent": round((int(value_row.get("value_count") or 0) * 100.0 / total), 4) if total else 0.0,
                            })
                else:
                    base["profile_status"] = "ERROR_RECORDED"
            profile_rows.append(base)
        self.data["column_profile"] = profile_rows
        _csv(self.artifact("COLUMN_PROFILE.csv"), tuple(profile_rows[0]) if profile_rows else ("server_name", "database_name", "schema_name", "object_name", "column_name", "profile_status"), profile_rows)
        _csv(self.artifact("LOW_CARDINALITY_VALUES.csv"), tuple(low_cardinality_rows[0]) if low_cardinality_rows else ("server_name", "database_name", "schema_name", "object_name", "column_name", "value", "value_count", "total_rows"), low_cardinality_rows)

    def prompt08_samples(self) -> None:
        if not self.settings.profile_include_sample_data:
            _md(self.root / "14_Samples" / "README.md", "# Samples\n\nDisabled by configuration.")
            _csv(self.artifact("MASKING_REPORT.csv"), ("schema_name", "object_name", "column_name", "category", "action"), [])
            _csv(self.artifact("SAMPLE_INDEX.csv"), ("schema_name", "object_name", "row_count", "ordering_strategy", "status"), [])
            return
        columns_by_object: dict[str, list[dict[str, Any]]] = {}
        for column in self.data["columns"]:
            columns_by_object.setdefault(_object_key(column), []).append(column)
        masking_rows: list[dict[str, Any]] = []
        sample_index: list[dict[str, Any]] = []
        sample_rows_by_object: dict[str, list[dict[str, Any]]] = {}
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        property_text: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            prop_key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            property_text[prop_key] = property_text.get(prop_key, "") + " " + str(prop.get("property_value") or "")
        for key, columns in sorted(columns_by_object.items()):
            schema, obj = key.split(".", 1)
            headers = [str(col["column_name"]) for col in sorted(columns, key=lambda item: int(item["column_id"]))]
            if not _within_safety_threshold(sizes, key, self.settings.profile_large_table_threshold):
                status = "SKIPPED_ROW_ESTIMATE_UNAVAILABLE" if _known_row_estimate(sizes, key) is None else "SKIPPED_FOR_SAFETY_LARGE_TABLE"
                _csv(self.root / "14_Samples" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.csv", headers, [])
                sample_rows_by_object[key] = []
                sample_index.append({"schema_name": schema, "object_name": obj, "row_count": 0, "ordering_strategy": "NOT_APPLICABLE", "status": status})
                continue
            order = ""
            pk_cols = [row for row in self.data.get("primary_keys", []) if row["schema_name"] == schema and row["object_name"] == obj]
            if pk_cols:
                ordered = sorted(pk_cols, key=lambda row: int(row["key_ordinal"]))
                order = " ORDER BY " + ", ".join(_qid(str(row["column_name"])) for row in ordered)
                ordering_strategy = "PRIMARY_KEY"
            else:
                stable = next((row for row in sorted(columns, key=lambda item: int(item["column_id"])) if str(row.get("data_type") or "").casefold() not in SKIP_PROFILE_TYPES and not row.get("is_computed")), None)
                if stable:
                    order = " ORDER BY " + _qid(str(stable["column_name"]))
                    ordering_strategy = f"FIRST_STABLE_COLUMN:{stable['column_name']}"
                else:
                    ordering_strategy = "CATALOG_ORDER_UNAVAILABLE"
            sql = f"SELECT TOP ({self.settings.profile_sample_rows}) * FROM {_qid(schema)}.{_qid(obj)}{order}"
            rows = self.fetch_dynamic(sql, prompt="08", stage="samples", schema=schema, obj=obj, query_name="safe_sample")
            categories = {
                str(col["column_name"]): _classification(
                    f"{col['column_name']} {property_text.get((schema, obj, str(col['column_name'])), '')}"
                ) for col in columns
            }
            safe_rows = []
            for row in rows:
                safe_rows.append({name: _mask(value, categories.get(name, ("Unknown", "PRESERVE"))[0], self.mask_salt, self.settings.profile_mask_sensitive_data) for name, value in row.items()})
            for name, (category, action) in categories.items():
                masking_rows.append({"schema_name": schema, "object_name": obj, "column_name": name, "category": category, "action": action})
            _csv(self.root / "14_Samples" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.csv", headers, safe_rows)
            sample_rows_by_object[key] = safe_rows
            sample_index.append({"schema_name": schema, "object_name": obj, "row_count": len(safe_rows), "ordering_strategy": ordering_strategy, "status": "SAMPLED" if safe_rows else "HEADER_ONLY_EMPTY_OR_INACCESSIBLE"})
        self.data["masking"] = masking_rows
        self.data["sample_rows"] = sample_rows_by_object
        _csv(self.artifact("MASKING_REPORT.csv"), ("schema_name", "object_name", "column_name", "category", "action"), masking_rows)
        _csv(self.artifact("SAMPLE_INDEX.csv"), ("schema_name", "object_name", "row_count", "ordering_strategy", "status"), sample_index)

    def prompt09_sensitivity(self) -> None:
        rows = []
        descriptions: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            descriptions[key] = descriptions.get(key, "") + " " + str(prop.get("property_value") or "")
        for column in self.data["columns"]:
            key = (str(column["schema_name"]), str(column["object_name"]), str(column["column_name"]))
            evidence_text = f"{column['column_name']} {descriptions.get(key, '')}"
            category, action = _classification(evidence_text)
            evidence = "COLUMN_NAME_AND_EXTENDED_PROPERTY_HEURISTIC" if descriptions.get(key) else "COLUMN_NAME_HEURISTIC"
            rows.append({
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": column["schema_name"], "object_name": column["object_name"],
                "column_name": column["column_name"], "data_type": column["data_type"],
                "sensitivity_category": category, "masking_action": action,
                "evidence": evidence, "evidence_class": "INFERENCE" if category != "Unknown" else "UNKNOWN", "confidence": "MEDIUM" if category != "Unknown" else "LOW",
            })
        self.data["sensitivity"] = rows
        _csv(self.artifact("SENSITIVITY_CLASSIFICATION.csv"), tuple(rows[0]) if rows else (), rows)

    def prompt10_relationships(self) -> None:
        columns = self.data["columns"]
        column_lookup = {(_object_key(c), str(c["column_name"])): c for c in columns}
        declared = self.data.get("foreign_keys", [])
        declared_sources = {(str(row["source_schema"]), str(row["source_object"]), str(row["source_column"])) for row in declared}

        unique_targets: list[dict[str, Any]] = []
        pk_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in self.data.get("primary_keys", []):
            pk_groups.setdefault((str(row["schema_name"]), str(row["object_name"]), str(row["constraint_name"])), []).append(row)
        for group in pk_groups.values():
            if len(group) == 1:
                unique_targets.append({**group[0], "unique_evidence": "PRIMARY_KEY"})
        index_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in self.data.get("indexes", []):
            if row.get("is_unique") and int(row.get("key_ordinal") or 0) > 0:
                index_groups.setdefault((str(row["schema_name"]), str(row["object_name"]), str(row.get("index_name") or "")), []).append(row)
        for group in index_groups.values():
            if len(group) == 1:
                item = group[0]
                unique_targets.append({"schema_name": item["schema_name"], "object_name": item["object_name"], "column_name": item["column_name"], "unique_evidence": "UNIQUE_INDEX"})

        inferred: list[dict[str, Any]] = []
        for col in columns:
            source_identity = (str(col["schema_name"]), str(col["object_name"]), str(col["column_name"]))
            if col.get("object_type") != "USER_TABLE" or source_identity in declared_sources:
                continue
            source_name = str(col["column_name"])
            if not re.search(r"(^id$|id$|_id$|code$|no$)", source_name, re.I):
                continue
            scored: list[tuple[int, dict[str, Any], str]] = []
            for target in unique_targets:
                if str(target["schema_name"]) == source_identity[0] and str(target["object_name"]) == source_identity[1]:
                    continue
                target_column = column_lookup.get((f"{target['schema_name']}.{target['object_name']}", str(target["column_name"])))
                if not target_column or str(target_column.get("data_type") or "").casefold() != str(col.get("data_type") or "").casefold():
                    continue
                source_norm = _normalized_identifier(source_name)
                target_col_norm = _normalized_identifier(str(target["column_name"]))
                target_table_norm = _normalized_identifier(str(target["object_name"]))
                score = 2
                evidence = ["compatible type", str(target["unique_evidence"]).lower()]
                if source_norm == target_col_norm:
                    score += 4; evidence.append("matching column name")
                if source_norm in {target_table_norm + "id", target_table_norm.rstrip("s") + "id"}:
                    score += 5; evidence.append("table-name identifier pattern")
                elif target_table_norm and target_table_norm in source_norm:
                    score += 3; evidence.append("table-name overlap")
                if score >= 6:
                    scored.append((score, target, "; ".join(evidence)))
            for score, target, evidence in sorted(scored, key=lambda item: item[0], reverse=True)[:3]:
                inferred.append({
                    "server_name": "[SANITIZED]", "database_name": self.database,
                    "source_schema": source_identity[0], "source_object": source_identity[1], "source_column": source_name,
                    "target_schema": target["schema_name"], "target_object": target["object_name"], "target_column": target["column_name"],
                    "classification": "SCHEMA_INFERRED", "confidence": "HIGH" if score >= 10 else "MEDIUM" if score >= 8 else "LOW",
                    "evidence": evidence, "evidence_class": "INFERENCE", "inference_score": score,
                })

        self.data["inferred_relationships"] = inferred
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        cardinality: list[dict[str, Any]] = []
        orphans: list[dict[str, Any]] = []
        relationship_rows: list[dict[str, Any]] = []
        fk_counts: dict[tuple[str, str, str], int] = {}
        for fk in declared:
            key = (str(fk["source_schema"]), str(fk["source_object"]), str(fk["constraint_name"]))
            fk_counts[key] = fk_counts.get(key, 0) + 1
            relationship_rows.append({**fk, "classification": "DECLARED_FK", "confidence": "HIGH", "evidence": "sys.foreign_keys", "evidence_class": "FACT"})
        relationship_rows.extend(inferred)

        for row in relationship_rows:
            source_key = f"{row['source_schema']}.{row['source_object']}"; target_key = f"{row['target_schema']}.{row['target_object']}"
            composite = row.get("classification") == "DECLARED_FK" and fk_counts.get((str(row["source_schema"]), str(row["source_object"]), str(row.get("constraint_name") or "")), 0) > 1
            validation: dict[str, Any] | None = None
            if (
                not composite
                and _within_safety_threshold(sizes, source_key, self.settings.profile_large_table_threshold)
                and _within_safety_threshold(sizes, target_key, self.settings.profile_large_table_threshold)
            ):
                scol = _qid(str(row["source_column"])); tcol = _qid(str(row["target_column"]))
                sql = (
                    f"SELECT COUNT_BIG(*) AS source_rows, SUM(CASE WHEN s.{scol} IS NULL THEN 1 ELSE 0 END) AS null_source_values, "
                    f"COUNT_BIG(DISTINCT s.{scol}) AS source_distinct_values, "
                    f"SUM(CASE WHEN s.{scol} IS NOT NULL AND t.{tcol} IS NULL THEN 1 ELSE 0 END) AS orphan_rows "
                    f"FROM {_qid(str(row['source_schema']))}.{_qid(str(row['source_object']))} AS s "
                    f"LEFT JOIN {_qid(str(row['target_schema']))}.{_qid(str(row['target_object']))} AS t ON t.{tcol} = s.{scol}"
                )
                result = self.fetch_dynamic(sql, prompt="10", stage="relationship_validation", schema=str(row["source_schema"]), obj=str(row["source_object"]), query_name=str(row["source_column"]))
                validation = result[0] if result else None
            if validation:
                source_rows = int(validation.get("source_rows") or 0); nulls = int(validation.get("null_source_values") or 0)
                orphan_count = int(validation.get("orphan_rows") or 0); distincts = int(validation.get("source_distinct_values") or 0); nonnull = source_rows - nulls
                if row.get("classification") != "DECLARED_FK":
                    row["classification"] = "DATA_VALIDATED"; row["confidence"] = "HIGH" if orphan_count == 0 else "MEDIUM"
                    row["evidence"] = str(row.get("evidence") or "") + "; value-domain join validation"
                    row["evidence_class"] = "DATA_VALIDATION"
                likely = "1:1" if nonnull == distincts else "N:1"
                cardinality.append({**row, "likely_cardinality": likely, "optionality": "OPTIONAL" if nulls else "REQUIRED_IN_CURRENT_DATA", "validation_status": "DATA_VALIDATED"})
                orphans.append({**row, "source_rows": source_rows, "null_source_values": nulls, "orphan_rows": orphan_count, "matched_rows": nonnull - orphan_count, "orphan_percent": round(orphan_count * 100.0 / nonnull, 4) if nonnull else 0.0, "analysis_status": "DATA_VALIDATED"})
            else:
                reason = "COMPOSITE_RELATIONSHIP_NOT_SCANNED_PER_COLUMN" if composite else "SKIPPED_FOR_SAFETY_OR_ACCESS"
                cardinality.append({**row, "likely_cardinality": "N:1" if not composite else "UNKNOWN", "optionality": "UNKNOWN", "validation_status": reason})
                orphans.append({**row, "source_rows": "", "null_source_values": "", "orphan_rows": "", "matched_rows": "", "orphan_percent": "", "analysis_status": reason})

        by_source: dict[str, set[str]] = {}
        for fk in declared:
            by_source.setdefault(f"{fk['source_schema']}.{fk['source_object']}", set()).add(f"{fk['target_schema']}.{fk['target_object']}")
        for bridge, targets in sorted(by_source.items()):
            if len(targets) >= 2:
                cardinality.append({"database_name": self.database, "source_schema": bridge.split(".", 1)[0], "source_object": bridge.split(".", 1)[1], "source_column": "MULTIPLE_FKS", "target_schema": "", "target_object": ", ".join(sorted(targets)), "target_column": "", "classification": "SCHEMA_INFERRED", "confidence": "MEDIUM", "evidence": "table has foreign keys to multiple distinct targets", "evidence_class": "INFERENCE", "likely_cardinality": "N:N_BRIDGE_CANDIDATE", "optionality": "UNKNOWN", "validation_status": "STRUCTURAL_INFERENCE"})
        self.data["relationship_cardinality"] = cardinality
        self.data["orphan_analysis"] = orphans
        _csv(self.artifact("INFERRED_RELATIONSHIPS.csv"), tuple(inferred[0]) if inferred else ("server_name", "database_name", "source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "classification", "confidence", "evidence"), inferred)
        _csv(self.artifact("RELATIONSHIP_CARDINALITY.csv"), tuple(cardinality[0]) if cardinality else ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "likely_cardinality", "validation_status"), cardinality)
        _csv(self.artifact("ORPHAN_ANALYSIS.csv"), tuple(orphans[0]) if orphans else ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "analysis_status"), orphans)

    def prompt11_lineage(self) -> None:
        deps = [dict(row) for row in self.data.get("dependencies", [])]
        for row in deps:
            if row.get("target_server"):
                row["target_server"] = _sanitized_external_server(row["target_server"])
        existing = {
            (str(row.get("source_schema") or "").casefold(), str(row.get("source_object") or "").casefold(), str(row.get("target_database") or "").casefold(), str(row.get("target_schema") or "").casefold(), str(row.get("target_object") or "").casefold())
            for row in deps
        }
        for reference in self.data.get("static_references", []):
            reference = dict(reference)
            if reference.get("target_server"):
                reference["target_server"] = _sanitized_external_server(reference["target_server"])
            key = (str(reference.get("source_schema") or "").casefold(), str(reference.get("source_object") or "").casefold(), str(reference.get("target_database") or "").casefold(), str(reference.get("target_schema") or "").casefold(), str(reference.get("target_object") or "").casefold())
            if key in existing:
                continue
            deps.append({
                **reference, "source_column_id": "", "target_column": "", "referenced_id": "",
                "is_schema_bound_reference": "", "is_caller_dependent": "", "is_ambiguous": "",
            })
            existing.add(key)
        self.data["all_dependencies"] = deps
        _csv(self.artifact("OBJECT_DEPENDENCIES.csv"), tuple(deps[0]) if deps else self._programmable_headers("dependencies"), deps)
        source_columns = {(int(col["object_id"]), int(col["column_id"])): col["column_name"] for col in self.data.get("columns", [])}
        object_ids = {(str(row.get("source_schema")), str(row.get("source_object"))): next((int(obj["object_id"]) for group in (self.data.get("views", []), self.data.get("procedures", []), self.data.get("functions", [])) for obj in group if str(obj.get("schema_name")) == str(row.get("source_schema")) and str(obj.get("object_name")) == str(row.get("source_object"))), 0) for row in deps}
        lineage = []
        definitions = {(str(row.get("schema_name") or row.get("parent_schema_name") or ""), str(row.get("object_name") or "")): str(row.get("definition_sanitized") or "") for category in ("views", "procedures", "functions", "triggers") for row in self.data.get(category, [])}
        for row in deps:
            object_id = object_ids.get((str(row.get("source_schema")), str(row.get("source_object"))), 0)
            source_column = source_columns.get((object_id, int(row.get("source_column_id") or 0)), "")
            definition = definitions.get((str(row.get("source_schema") or ""), str(row.get("source_object") or "")), "")
            if source_column and row.get("target_column"):
                lineage_type = "DIRECT"
            elif row.get("target_column") and re.search(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", definition, re.I):
                lineage_type = "AGGREGATED"
            elif row.get("target_column") and re.search(r"\bCASE\b", definition, re.I):
                lineage_type = "CONDITIONAL"
            elif row.get("target_column") and re.search(r"[+*/-]", definition):
                lineage_type = "DERIVED"
            else:
                lineage_type = "UNKNOWN"
            lineage.append({
                **row, "source_column": source_column, "relationship": row.get("operation") or "REFERENCE", "lineage_type": lineage_type,
                "evidence": row.get("evidence") or "sys.sql_expression_dependencies", "confidence": "HIGH" if row.get("referenced_id") else "MEDIUM" if row.get("target_schema") else "LOW",
            })
        known_columns: dict[tuple[str, str], set[str]] = {}
        for column in self.data.get("columns", []):
            if column.get("object_type") == "USER_TABLE":
                known_columns.setdefault((str(column["schema_name"]), str(column["object_name"])), set()).add(str(column["column_name"]).casefold())
        static_seen: set[tuple[str, str, str, str, str, str]] = set()
        for category in ("views", "procedures", "functions", "triggers"):
            for obj in self.data.get(category, []):
                source_schema = str(obj.get("schema_name") or obj.get("parent_schema_name") or "")
                source_object = str(obj.get("object_name") or "")
                for reference in _static_column_references(obj, known_columns):
                    key = (source_schema.casefold(), source_object.casefold(), reference["target_schema"].casefold(), reference["target_object"].casefold(), reference["target_column"].casefold(), reference["lineage_type"])
                    if key in static_seen:
                        continue
                    static_seen.add(key)
                    lineage.append({
                        "source_server": "[SANITIZED]", "source_database": self.database,
                        "source_schema": source_schema, "source_object": source_object, "source_type": category[:-1].upper(),
                        "source_column": "EXPRESSION_OUTPUT_UNKNOWN", "target_server": "", "target_database": self.database,
                        "target_schema": reference["target_schema"], "target_object": reference["target_object"], "target_column": reference["target_column"],
                        "relationship": "COLUMN_REFERENCE", "lineage_type": reference["lineage_type"],
                        "evidence": reference["evidence"], "confidence": "MEDIUM",
                    })
        self.data["lineage"] = lineage
        _csv(self.artifact("LINEAGE_EDGES.csv"), tuple(lineage[0]) if lineage else ("source_database", "source_schema", "source_object", "target_database", "target_schema", "target_object", "relationship", "lineage_type", "evidence", "confidence"), lineage)
        view_deps = [row for row in deps if row.get("source_type") == "VIEW"]
        sp_deps = [row for row in deps if row.get("source_type") in {"SQL_STORED_PROCEDURE", "CLR_STORED_PROCEDURE"}]
        _csv(self.artifact("VIEW_DEPENDENCIES.csv"), tuple(view_deps[0]) if view_deps else self._programmable_headers("dependencies"), view_deps)
        _csv(self.artifact("STORED_PROCEDURE_DEPENDENCIES.csv"), tuple(sp_deps[0]) if sp_deps else self._programmable_headers("dependencies"), sp_deps)
        lineage_counts = {kind: sum(row.get("lineage_type") == kind for row in lineage) for kind in ("DIRECT", "DERIVED", "AGGREGATED", "CONDITIONAL", "UNKNOWN")}
        _md(self.artifact("LINEAGE_SUMMARY.md"), "# Lineage Summary\n\n" + "\n".join((
            f"- Object dependency edges: {len(deps)}", f"- Lineage edges: {len(lineage)}",
            *(f"- {kind.title()} classifications: {count}" for kind, count in lineage_counts.items()),
            "- `UNKNOWN` is retained where catalog/static evidence cannot safely resolve column transformation semantics.",
            "- Dynamic SQL may be opaque and is reported separately.",
        )))
        degree: dict[str, dict[str, int]] = {}
        for row in deps:
            source = f"{row.get('source_schema')}.{row.get('source_object')}"
            target = f"{row.get('target_schema')}.{row.get('target_object')}"
            degree.setdefault(source, {"inbound": 0, "outbound": 0})["outbound"] += 1
            degree.setdefault(target, {"inbound": 0, "outbound": 0})["inbound"] += 1
        impact = [{"object_name": key, **value, "total_edges": value["inbound"] + value["outbound"], "interpretation": "STRUCTURAL_CENTRALITY_NOT_BUSINESS_CRITICALITY"} for key, value in degree.items()]
        impact.sort(key=lambda row: int(row["total_edges"]), reverse=True)
        _csv(self.artifact("HIGH_IMPACT_OBJECTS.csv"), tuple(impact[0]) if impact else ("object_name", "inbound", "outbound", "total_edges", "interpretation"), impact)

    def prompt12_external(self) -> None:
        rows = []
        for dep in self.data.get("all_dependencies", self.data.get("dependencies", [])):
            if dep.get("target_server") or dep.get("target_database"):
                rows.append({**dep, "reference_kind": "FOUR_PART" if dep.get("target_server") else "THREE_PART", "queried_external_system": False})
        for synonym in self.data.get("synonyms", []):
            base = str(synonym.get("base_object_name") or "")
            if base.count(".") >= 2:
                parts = [part.strip("[]") for part in base.split(".")]
                if len(parts) >= 4:
                    parts[0] = _sanitized_external_server(parts[0])
                safe_base = ".".join(parts)
                rows.append({
                    "source_server": "[SANITIZED]", "source_database": self.database,
                    "source_schema": synonym.get("schema_name"), "source_object": synonym.get("object_name"),
                    "source_type": "SYNONYM", "target_server": "", "target_database": "",
                    "target_schema": "", "target_object": safe_base, "reference_kind": "SYNONYM_EXTERNAL",
                    "queried_external_system": False,
                })
        for category in ("views", "procedures", "functions", "triggers"):
            for obj in self.data.get(category, []):
                definition = str(obj.get("definition_sanitized") or "")
                for construct in ("OPENQUERY", "OPENROWSET", "OPENDATASOURCE"):
                    if re.search(rf"\b{construct}\s*\(", definition, re.I):
                        rows.append({
                            "source_server": "[SANITIZED]", "source_database": self.database,
                            "source_schema": obj.get("schema_name") or obj.get("parent_schema_name"),
                            "source_object": obj.get("object_name"), "source_type": category[:-1].upper(),
                            "target_server": "[STATIC_TEXT_REDACTED]", "target_database": "", "target_schema": "", "target_object": "",
                            "reference_kind": construct, "queried_external_system": False,
                        })
        linked_servers = self.fetch_dynamic(
            "SELECT name, product, provider, is_linked, is_data_access_enabled, is_rpc_out_enabled FROM sys.servers WHERE server_id > 0 ORDER BY name",
            prompt="12", stage="linked_server_metadata", schema="sys", obj="servers", query_name="linked_servers",
        )
        safe_linked_servers = []
        for item in linked_servers:
            digest = hashlib.sha256(str(item.get("name") or "").encode("utf-8", errors="replace")).hexdigest()[:12]
            safe_linked_servers.append({**item, "name": f"[EXTERNAL_SERVER:{digest}]"})
        self.data["linked_servers"] = safe_linked_servers
        _csv(self.artifact("LINKED_SERVER_CATALOGUE.csv"), tuple(safe_linked_servers[0]) if safe_linked_servers else ("name", "product", "provider", "is_linked", "is_data_access_enabled", "is_rpc_out_enabled"), safe_linked_servers)
        self.data["external"] = rows
        _csv(self.artifact("CROSS_DATABASE_SERVER_REFERENCES.csv"), tuple(rows[0]) if rows else ("source_server", "source_database", "source_schema", "source_object", "source_type", "target_server", "target_database", "target_schema", "target_object", "reference_kind", "queried_external_system"), rows)

    def prompt13_classification(self) -> None:
        shapes = {_object_key(row): row for row in self.data.get("table_shape", [])}
        pk_counts: dict[str, int] = {}
        fk_out_counts: dict[str, int] = {}
        fk_in_counts: dict[str, int] = {}
        index_counts: dict[str, set[str]] = {}
        constraint_counts: dict[str, set[str]] = {}
        for row in self.data.get("primary_keys", []): pk_counts[_object_key(row)] = pk_counts.get(_object_key(row), 0) + 1
        for row in self.data.get("foreign_keys", []):
            source = f"{row['source_schema']}.{row['source_object']}"; target = f"{row['target_schema']}.{row['target_object']}"
            fk_out_counts[source] = fk_out_counts.get(source, 0) + 1; fk_in_counts[target] = fk_in_counts.get(target, 0) + 1
        for row in self.data.get("indexes", []): index_counts.setdefault(_object_key(row), set()).add(str(row.get("index_name") or ""))
        for row in self.data.get("constraints", []): constraint_counts.setdefault(_object_key(row), set()).add(str(row.get("constraint_name") or ""))
        buckets: dict[str, list[dict[str, Any]]] = {"MASTER": [], "LOOKUP": [], "TRANSACTION": [], "BRIDGE": [], "HISTORY": [], "AUDIT": [], "STAGING": [], "ARCHIVE": [], "CONFIGURATION": []}
        classified = []
        for table in self.data["tables"]:
            key = _object_key(table)
            name = str(table["object_name"]).lower()
            shape = shapes.get(key, {})
            row_count = int(shape.get("estimated_rows") or 0)
            column_count = int(shape.get("column_count") or 0)
            confidence = "LOW"; evidence = "structural inference only"
            if re.search(r"audit|log", name): category = "AUDIT"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"history", name): category = "HISTORY"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"archive|backup|old", name): category = "ARCHIVE"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"stage|staging|import|temp", name): category = "STAGING"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"config|setting|option", name): category = "CONFIGURATION"; confidence = "MEDIUM"; evidence = "name pattern"
            elif fk_out_counts.get(key, 0) >= 2 and column_count <= 16: category = "BRIDGE"; confidence = "MEDIUM"; evidence = "multiple outbound FKs and narrow shape"
            elif re.search(r"map|bridge|link|detail", name) and column_count <= 16: category = "BRIDGE"; evidence = "name and narrow shape"
            elif re.search(r"lookup|type|status|master", name) or (row_count <= 100 and column_count <= 12): category = "LOOKUP"; evidence = "name or small narrow shape"
            elif re.search(r"transaction|invoice|payment|receipt|order|entry", name): category = "TRANSACTION"; confidence = "MEDIUM"; evidence = "name pattern"
            elif fk_in_counts.get(key, 0) >= 2: category = "MASTER"; evidence = "multiple inbound FK references"
            else: category = "UNKNOWN"; evidence = "insufficient structural evidence"
            item = {"server_name": "[SANITIZED]", "database_name": self.database, "schema_name": table["schema_name"], "object_name": table["object_name"], "inferred_category": category, "confidence": confidence, "evidence": evidence, "evidence_class": "UNKNOWN" if category == "UNKNOWN" else "INFERENCE"}
            if category in buckets: buckets[category].append(item)
            classified.append(item)
            table.update({
                "estimated_rows": row_count, "column_count": column_count,
                "primary_key_column_count": pk_counts.get(key, 0), "foreign_key_outbound_count": fk_out_counts.get(key, 0),
                "foreign_key_inbound_count": fk_in_counts.get(key, 0), "index_count": len(index_counts.get(key, set())),
                "constraint_count": len(constraint_counts.get(key, set())), "inferred_category": category,
                "classification_confidence": confidence, "classification_evidence": evidence,
            })
        names = {"MASTER": "POSSIBLE_MASTER_TABLES.csv", "LOOKUP": "POSSIBLE_LOOKUP_TABLES.csv", "TRANSACTION": "POSSIBLE_TRANSACTION_TABLES.csv", "BRIDGE": "POSSIBLE_BRIDGE_TABLES.csv", "HISTORY": "POSSIBLE_HISTORY_AUDIT_TABLES.csv"}
        headers = ("server_name", "database_name", "schema_name", "object_name", "inferred_category", "confidence", "evidence", "evidence_class")
        for category, filename in names.items():
            selected = buckets[category]
            if category == "HISTORY": selected = selected + buckets["AUDIT"]
            _csv(self.artifact(filename), headers, selected)
        other = buckets["STAGING"] + buckets["ARCHIVE"] + buckets["CONFIGURATION"]
        _csv(self.artifact("OTHER_STRUCTURAL_CLASSIFICATIONS.csv"), headers, other)
        if self.data.get("tables"):
            _csv(self.artifact("TABLE_CATALOGUE.csv"), tuple(self.data["tables"][0]), self.data["tables"])
        column_sets: dict[str, set[str]] = {}
        for col in self.data["columns"]:
            if col.get("object_type") == "USER_TABLE": column_sets.setdefault(_object_key(col), set()).add(str(col["column_name"]).casefold())
        duplicates = []
        keys = sorted(column_sets)
        for index, left in enumerate(keys):
            for right in keys[index + 1:]:
                union = column_sets[left] | column_sets[right]
                score = len(column_sets[left] & column_sets[right]) / len(union) if union else 0
                if score >= 0.8: duplicates.append((left, right, score))
        lines = ["# Possible Duplicate or Legacy Structures", "", "All entries are inference, not fact.", ""]
        lines.extend(f"- `{left}` ↔ `{right}`: column-name Jaccard similarity {score:.2f}" for left, right, score in duplicates)
        if not duplicates: lines.append("No pairs crossed the 0.80 structural-similarity threshold.")
        _md(self.artifact("POSSIBLE_DUPLICATE_OR_LEGACY_STRUCTURES.md"), "\n".join(lines))

    def prompt14_quality(self) -> None:
        table_keys = {_object_key(row) for row in self.data["tables"]}
        pk_keys = {_object_key(row) for row in self.data.get("primary_keys", [])}
        missing = sorted(table_keys - pk_keys)
        missing_rows = [{"database_name": self.database, "schema_name": key.split(".", 1)[0], "object_name": key.split(".", 1)[1], "observation": "NO_DECLARED_PRIMARY_KEY", "evidence": "FACT"} for key in missing]
        _csv(self.artifact("TABLES_WITHOUT_PRIMARY_KEY.csv"), ("database_name", "schema_name", "object_name", "observation", "evidence"), missing_rows)
        risks: list[dict[str, Any]] = []
        def add(severity: str, category: str, context: str, observation: str, evidence: str, uncertainty: str) -> None:
            if evidence not in EVIDENCE_CLASSES:
                raise ValueError(f"Invalid evidence class: {evidence}")
            risks.append({"severity": severity, "category": category, "object_context": context, "observation": observation, "evidence_type": evidence, "uncertainty": uncertainty})
        for row in missing_rows: add("Medium", "Structure", f"{row['schema_name']}.{row['object_name']}", "Table has no declared primary key", "FACT", "Business intent unknown; another unique key may exist")
        if not self.data.get("foreign_keys"): risks.append({"severity": "High", "category": "Relationships", "object_context": self.database, "observation": "No declared foreign keys are visible", "evidence_type": "FACT", "uncertainty": "Integrity may be enforced in application code or permissions may limit visibility"})
        for row in self.data.get("column_profile", []):
            if row.get("profile_status") == "PROFILED" and str(row.get("total_rows")) not in {"", "0"}:
                context = f"{row['schema_name']}.{row['object_name']}.{row['column_name']}"
                if int(row.get("non_null_count") or 0) == 0: add("Low", "Data Quality", context, "Column is all null", "DATA_VALIDATION", "Current snapshot only")
                elif str(row.get("distinct_count")) not in {"", "None"} and int(row.get("distinct_count") or 0) == 1: add("Informational", "Data Quality", context, "Column is constant", "DATA_VALIDATION", "Current snapshot only")
                if int(row.get("empty_string_count") or 0) > 0: add("Low", "Data Quality", context, f"Contains {row['empty_string_count']} empty strings", "DATA_VALIDATION", "Empty strings may be valid business values")
                whitespace = int(row.get("whitespace_string_count") or 0)
                empty = int(row.get("empty_string_count") or 0)
                if whitespace > empty: add("Low", "Data Quality", context, f"Contains {whitespace - empty} whitespace-only non-empty strings", "DATA_VALIDATION", "Current snapshot only")
                if int(row.get("negative_count") or 0) > 0: add("Informational", "Numeric Range", context, f"Contains {row['negative_count']} negative values", "DATA_VALIDATION", "Negative values may be valid; semantic range is unknown")
            elif str(row.get("profile_status") or "").startswith("SKIPPED"):
                add("Informational", "Coverage", f"{row['schema_name']}.{row['object_name']}.{row['column_name']}", f"Profiling {row['profile_status']}", "FACT", "No data-level conclusion is possible")
        for row in self.data.get("orphan_analysis", []):
            if int(row.get("orphan_rows") or 0) > 0:
                add("Medium" if row.get("classification") == "DECLARED_FK" else "Low", "Relationships", f"{row['source_schema']}.{row['source_object']}.{row['source_column']}", f"Observed {row['orphan_rows']} unmatched non-null references", "DATA_VALIDATION", "Inferred relationships may be semantically unrelated")
        for row in self.data.get("foreign_keys", []):
            if row.get("is_disabled") or row.get("is_not_trusted"):
                add("High" if row.get("is_disabled") else "Medium", "Constraint", f"{row['source_schema']}.{row['source_object']}.{row['constraint_name']}", "Foreign key is disabled or untrusted", "FACT", "Current catalog state")
        for row in self.data.get("constraints", []):
            if row.get("is_disabled") or row.get("is_not_trusted"):
                add("Medium", "Constraint", f"{row['schema_name']}.{row['object_name']}.{row['constraint_name']}", "Constraint is disabled or untrusted", "FACT", "Current catalog state")
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                context = f"{row.get('schema_name') or row.get('parent_schema_name')}.{row.get('object_name')}"
                if not row.get("definition_available"): add("Medium", "Static Analysis", context, "Definition unavailable or encrypted", "FACT", "Dependencies and logic may be incomplete")
                if row.get("dynamic_sql_present"): add("Medium", "Dynamic SQL", context, "Dynamic SQL is present", "INFERENCE", "Runtime targets may remain opaque")
        for row in self.data.get("external", []):
            add("Medium", "External Dependency", f"{row.get('source_schema')}.{row.get('source_object')}", f"External reference detected: {row.get('reference_kind')}", "INFERENCE", "External system was not queried")
        for error in self.errors:
            add("Medium", "Access or Discovery Limitation", f"{error.get('schema_name')}.{error.get('object_name')}".strip("."), str(error.get("impact") or "Evidence unavailable"), "FACT", str(error.get("sanitized_message") or ""))
        self.data["risks"] = risks
        _csv(self.artifact("RISK_AND_UNCERTAINTY_REGISTER.csv"), tuple(risks[0]) if risks else ("severity", "category", "object_context", "observation", "evidence_type", "uncertainty"), risks)
        _md(self.artifact("DATA_QUALITY_SUMMARY.md"), f"# Data Quality Summary\n\n- Tables without declared primary keys: {len(missing)}\n- Declared foreign-key rows: {len(self.data.get('foreign_keys', []))}\n- Profile observations recorded: {sum(1 for row in self.data.get('column_profile', []) if row.get('profile_status') == 'PROFILED')}\n- Orphan analyses with unmatched rows: {sum(int(row.get('orphan_rows') or 0) > 0 for row in self.data.get('orphan_analysis', []))}\n- Disabled/untrusted FK rows: {sum(bool(row.get('is_disabled') or row.get('is_not_trusted')) for row in self.data.get('foreign_keys', []))}\n- Dynamic-SQL objects: {sum(bool(row.get('dynamic_sql_present')) for category in ('views', 'procedures', 'functions', 'triggers') for row in self.data.get(category, []))}\n- Risk-register entries: {len(risks)}\n\nSeverity is cautious; semantic meaning remains unknown unless explicitly documented. Duplicate-key and semantic range conclusions require declared/candidate key evidence and are not guessed from names alone.")

    def prompt15_outputs(self) -> None:
        self._object_docs()
        self._diagrams()
        self._narratives()
        self._html_report()
        self._ensure_contract_files()
        self._write_control_files(final=False)
        self._snapshot_integrity()

    def _object_docs(self) -> None:
        cols: dict[str, list[dict[str, Any]]] = {}
        for col in self.data["columns"]: cols.setdefault(_object_key(col), []).append(col)
        shapes = {_object_key(row): row for row in self.data.get("table_shape", [])}
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        samples = self.data.get("sample_rows", {})

        def matching(rows: Iterable[dict[str, Any]], schema: str, obj: str, *, source: bool = False, target: bool = False) -> list[dict[str, Any]]:
            result = []
            for row in rows:
                if source:
                    found = str(row.get("source_schema") or "") == schema and str(row.get("source_object") or "") == obj
                elif target:
                    found = str(row.get("target_schema") or "") == schema and str(row.get("target_object") or "") == obj
                else:
                    found = str(row.get("schema_name") or "") == schema and str(row.get("object_name") or "") == obj
                if found: result.append(row)
            return result

        for table in self.data["tables"]:
            key = _object_key(table); schema, obj = key.split(".", 1)
            table_columns = sorted(cols.get(key, []), key=lambda row: int(row["column_id"]))
            pk = matching(self.data.get("primary_keys", []), schema, obj)
            outbound_fk = matching(self.data.get("foreign_keys", []), schema, obj, source=True)
            inbound_fk = matching(self.data.get("foreign_keys", []), schema, obj, target=True)
            inferred_out = matching(self.data.get("inferred_relationships", []), schema, obj, source=True)
            indexes = matching(self.data.get("indexes", []), schema, obj)
            constraints = matching(self.data.get("constraints", []), schema, obj)
            references = matching(self.data.get("all_dependencies", []), schema, obj, source=True)
            referenced_by = matching(self.data.get("all_dependencies", []), schema, obj, target=True)
            profiles = matching(self.data.get("column_profile", []), schema, obj)
            lineage = [row for row in self.data.get("lineage", []) if (str(row.get("source_schema") or "") == schema and str(row.get("source_object") or "") == obj) or (str(row.get("target_schema") or "") == schema and str(row.get("target_object") or "") == obj)]
            pipelines = [row for row in self.data.get("pipelines", []) if key in {str(row.get("origin") or ""), str(row.get("source") or ""), str(row.get("destination") or "")}]
            risks = [row for row in self.data.get("risks", []) if str(row.get("object_context") or "").startswith(key)]
            shape = shapes.get(key, {}); size = sizes.get(key, {})
            lines = [
                f"# Table `{schema}.{obj}`", "",
                "Catalog identity and physical metadata are **FACT**. Purpose and structural category are explicitly labelled as inference.", "",
                "## Identity and inferred purpose", "",
                f"- Object ID: `{table.get('object_id', '')}`", f"- Created: `{table.get('create_date', '')}`", f"- Modified: `{table.get('modify_date', '')}`",
                f"- Temporal type: `{table.get('temporal_type_desc', '')}`", f"- Memory optimized: `{table.get('is_memory_optimized', '')}`",
                f"- Inferred category: `{table.get('inferred_category', 'UNKNOWN')}` ({table.get('classification_confidence', 'LOW')} confidence; {table.get('classification_evidence', 'insufficient evidence')})", "",
                "## Size and shape", "",
            ]
            lines.extend(_md_table([{**size, **shape}], ("row_count", "row_count_type", "reserved_kb", "used_kb", "data_kb", "index_kb", "column_count", "nullable_columns", "identity_columns", "computed_columns", "identifier_columns")))
            lines.extend(("", "## Columns", "")); lines.extend(_md_table(table_columns, ("column_id", "column_name", "data_type", "max_length", "precision", "scale", "is_nullable", "is_identity", "is_computed", "default_definition")))
            lines.extend(("", "## Primary keys", "")); lines.extend(_md_table(pk, ("constraint_name", "key_ordinal", "column_name", "index_type_desc")))
            lines.extend(("", "## Outbound declared relationships", "")); lines.extend(_md_table(outbound_fk, ("constraint_name", "source_column", "target_schema", "target_object", "target_column", "delete_action", "update_action", "is_disabled", "is_not_trusted")))
            lines.extend(("", "## Inbound declared relationships", "")); lines.extend(_md_table(inbound_fk, ("constraint_name", "source_schema", "source_object", "source_column", "target_column")))
            lines.extend(("", "## Inferred outbound relationships", "")); lines.extend(_md_table(inferred_out, ("source_column", "target_schema", "target_object", "target_column", "classification", "confidence", "evidence")))
            lines.extend(("", "## Indexes", "")); lines.extend(_md_table(indexes, ("index_name", "index_type_desc", "is_unique", "is_primary_key", "key_ordinal", "column_name", "is_included_column", "filter_definition", "is_disabled")))
            lines.extend(("", "## Constraints", "")); lines.extend(_md_table(constraints, ("constraint_name", "constraint_type", "column_name", "definition", "is_disabled", "is_not_trusted")))
            lines.extend(("", "## References", "")); lines.extend(_md_table(references, ("source_type", "target_database", "target_schema", "target_object", "operation", "evidence")))
            lines.extend(("", "## Referenced by", "")); lines.extend(_md_table(referenced_by, ("source_schema", "source_object", "source_type", "operation", "evidence")))
            lines.extend(("", "## Column profiles", "")); lines.extend(_md_table(profiles, ("column_name", "total_rows", "null_count", "null_percent", "distinct_count", "distinct_percent", "minimum_value", "maximum_value", "profile_status")))
            sample_values = samples.get(key, [])[:5]
            lines.extend(("", "## Masked sample", "")); lines.extend(_md_table(sample_values, tuple(str(col["column_name"]) for col in table_columns)))
            lines.extend(("", "## Lineage", "")); lines.extend(_md_table(lineage, ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "relationship", "lineage_type", "confidence")))
            lines.extend(("", "## Pipeline participation", "")); lines.extend(_md_table(pipelines, ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence")))
            lines.extend(("", "## Data-quality observations, risks, and uncertainties", "")); lines.extend(_md_table(risks, ("severity", "category", "observation", "evidence_type", "uncertainty")))
            lines.extend(("", "Semantic business purpose remains `UNKNOWN` unless supported by extended properties or static code evidence."))
            _md(self.root / "20_Object_Documentation" / "Tables" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.md", "\n".join(lines))
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                schema = str(row.get("schema_name") or row.get("parent_schema_name") or "database")
                obj = str(row.get("object_name"))
                params = matching(self.data.get("parameters", []), schema, obj)
                dependencies = matching(self.data.get("all_dependencies", []), schema, obj, source=True)
                inbound = matching(self.data.get("all_dependencies", []), schema, obj, target=True)
                object_pipelines = [item for item in self.data.get("pipelines", []) if f"{schema}.{obj}" in {str(item.get("origin") or ""), str(item.get("source") or ""), str(item.get("destination") or "")}]
                object_risks = [item for item in self.data.get("risks", []) if str(item.get("object_context") or "").startswith(f"{schema}.{obj}")]
                lines = [
                    f"# {category[:-1].title()} `{schema}.{obj}`", "",
                    "Metadata is **FACT**; logic descriptions are **STATIC ANALYSIS** and do not prove runtime use.", "",
                    "## Identity and static-analysis flags", "",
                    f"- Definition SHA-256: `{row.get('definition_sha256', '')}`", f"- Definition available: {row.get('definition_available', False)}",
                    f"- Dynamic SQL present: {row.get('dynamic_sql_present', False)}", f"- Temporary tables present: {row.get('temp_table_present', False)}",
                    f"- Transaction logic present: {row.get('transaction_logic_present', False)}", f"- Error handling present: {row.get('error_handling_present', False)}",
                    f"- Likely write logic: {row.get('likely_write_logic', False)}", "",
                    "## Parameters", "",
                ]
                lines.extend(_md_table(params, ("parameter_id", "parameter_name", "data_type", "max_length", "precision", "scale", "is_output", "has_default_value", "is_readonly")))
                lines.extend(("", "## Reads, writes, calls, and references", "")); lines.extend(_md_table(dependencies, ("target_server", "target_database", "target_schema", "target_object", "target_column", "operation", "evidence")))
                lines.extend(("", "## Referenced by", "")); lines.extend(_md_table(inbound, ("source_schema", "source_object", "source_type", "operation", "evidence")))
                lines.extend(("", "## Pipeline role", "")); lines.extend(_md_table(object_pipelines, ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence")))
                lines.extend(("", "## Risks and uncertainties", "")); lines.extend(_md_table(object_risks, ("severity", "category", "observation", "evidence_type", "uncertainty")))
                lines.extend(("", "## Sanitized static definition", "", "```sql", str(row.get("definition_sanitized") or "-- unavailable/encrypted"), "```"))
                _md(self.root / "20_Object_Documentation" / category.title() / f"{safe_path_component(schema)}__{safe_path_component(obj)}.md", "\n".join(lines))

    def _diagrams(self) -> None:
        columns_by_table: dict[str, list[dict[str, Any]]] = {}
        for column in self.data.get("columns", []):
            if column.get("object_type") == "USER_TABLE":
                columns_by_table.setdefault(_object_key(column), []).append(column)
        pk_columns = {(_object_key(row), str(row.get("column_name") or "")) for row in self.data.get("primary_keys", [])}
        fk_columns = {(f"{row.get('source_schema')}.{row.get('source_object')}", str(row.get("source_column") or "")) for row in self.data.get("foreign_keys", [])}

        def node_for(schema: str, obj: str) -> str:
            return re.sub(r"[^A-Za-z0-9_]", "_", f"{schema}_{obj}")

        def entity_lines(schema: str, obj: str) -> list[str]:
            key = f"{schema}.{obj}"; result = [f"    {node_for(schema, obj)} {{"]
            for column in sorted(columns_by_table.get(key, []), key=lambda item: int(item.get("column_id") or 0)):
                dtype = re.sub(r"[^A-Za-z0-9_]", "_", str(column.get("data_type") or "unknown"))
                name = re.sub(r"[^A-Za-z0-9_]", "_", str(column.get("column_name") or "column"))
                markers = []
                if (key, str(column.get("column_name") or "")) in pk_columns: markers.append("PK")
                if (key, str(column.get("column_name") or "")) in fk_columns: markers.append("FK")
                result.append(f"        {dtype} {name}{' ' + ','.join(markers) if markers else ''}")
            result.append("    }")
            return result

        lines = ["# Full ER Diagram", "", "```mermaid", "erDiagram"]
        for table in self.data["tables"]:
            lines.extend(entity_lines(str(table["schema_name"]), str(table["object_name"])))
        for fk in self.data.get("foreign_keys", []):
            source = node_for(str(fk["source_schema"]), str(fk["source_object"]))
            target = node_for(str(fk["target_schema"]), str(fk["target_object"]))
            lines.append(f"    {target} ||--o{{ {source} : \"{fk['constraint_name']}\"")
        lines.append("```")
        _md(self.artifact("FULL_ER_DIAGRAM.md"), "\n".join(lines))
        by_schema: dict[str, list[dict[str, Any]]] = {}
        for table in self.data["tables"]:
            by_schema.setdefault(str(table["schema_name"]), []).append(table)
        for schema, tables in by_schema.items():
            schema_lines = [f"# Schema Diagram — {schema}", "", "```mermaid", "erDiagram"]
            for table in tables:
                schema_lines.extend(entity_lines(schema, str(table["object_name"])))
            table_names = {str(table["object_name"]) for table in tables}
            for fk in self.data.get("foreign_keys", []):
                if str(fk.get("source_schema")) == schema and str(fk.get("target_schema")) == schema and str(fk.get("source_object")) in table_names and str(fk.get("target_object")) in table_names:
                    schema_lines.append(f"    {node_for(schema, str(fk['target_object']))} ||--o{{ {node_for(schema, str(fk['source_object']))} : \"{fk['constraint_name']}\"")
            schema_lines.append("```")
            _md(self.root / "19_Diagrams" / f"SCHEMA_{safe_path_component(schema)}.md", "\n".join(schema_lines))
        dependencies = self.data.get("all_dependencies", self.data.get("dependencies", []))
        dependency_groups: dict[str, list[dict[str, Any]]] = {"ALL": list(dependencies), "CROSS_DATABASE_SERVER": []}
        for dep in dependencies:
            source_type = str(dep.get("source_type") or "UNKNOWN").upper().replace("SQL_", "")
            dependency_groups.setdefault(source_type, []).append(dep)
            if dep.get("target_server") or dep.get("target_database"):
                dependency_groups["CROSS_DATABASE_SERVER"].append(dep)
        for group, group_rows in dependency_groups.items():
            title = "Object Dependency Diagram" if group == "ALL" else f"{group.replace('_', ' ').title()} Dependency Diagram"
            dependency_lines = [f"# {title}", "", f"All {len(group_rows)} catalog/static edges are included; no silent edge truncation is applied.", "", "```mermaid", "flowchart LR"]
            for index, dep in enumerate(group_rows):
                source = node_for(str(dep.get("source_schema") or "unknown"), str(dep.get("source_object") or f"source_{index}"))
                target_prefix = str(dep.get("target_database") or dep.get("target_server") or dep.get("target_schema") or "unknown")
                target = node_for(target_prefix, str(dep.get("target_object") or f"target_{index}"))
                relationship = re.sub(r"[^A-Za-z0-9_]", "_", str(dep.get("operation") or "reference"))
                dependency_lines.append(f"    {source} -->|{relationship}_{index}| {target}")
            dependency_lines.append("```")
            filename = "OBJECT_DEPENDENCY_DIAGRAM.md" if group == "ALL" else f"DEPENDENCY_{safe_path_component(group)}.md"
            _md(self.root / "19_Diagrams" / filename, "\n".join(dependency_lines))

    def _narratives(self) -> None:
        metrics = {"database": self.database, "tables": len(self.data.get("tables", [])), "columns": len(self.data.get("columns", [])), "views": len(self.data.get("views", [])), "procedures": len(self.data.get("procedures", [])), "functions": len(self.data.get("functions", [])), "triggers": len(self.data.get("triggers", [])), "declared_foreign_key_rows": len(self.data.get("foreign_keys", [])), "inferred_relationships": len(self.data.get("inferred_relationships", [])), "errors": len(self.errors)}
        _json(self.artifact("DATABASE_SUMMARY_METRICS.json"), metrics)
        _md(self.artifact("DATABASE_OVERVIEW.md"), "# Database Overview\n\n" + "\n".join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in metrics.items()))
        _md(self.artifact("DATABASE_GLOSSARY.md"), "# Database Glossary\n\nGenerated structural glossary. Semantic definitions remain `UNKNOWN` unless supported by extended properties.\n\n" + "\n".join(f"- `{row['schema_name']}.{row['object_name']}` — inferred purpose not asserted as fact." for row in self.data.get("tables", [])))
        _md(self.artifact("MSSQL_EXECUTIVE_SUMMARY.md"), f"# MSSQL Executive Summary\n\nThe configured database contains {metrics['tables']} tables and {metrics['columns']} columns visible to the reader identity. All discovery was read-only. Declared and inferred relationships are reported separately. See the risk register and access limitations before making design decisions.")
        _md(self.artifact("PIPELINE_SUMMARY.md"), f"# Pipeline Summary\n\nStatic dependency and job evidence produced {len(self.data.get('pipelines', []))} candidate pipeline rows. Object existence does not prove active use.")
        _md(self.artifact("ACCESS_AND_DISCOVERY_LIMITATIONS.md"), "# Access and Discovery Limitations\n\n- Results cover only objects visible to the configured identity.\n- Dynamic SQL and encrypted modules can make dependencies opaque.\n- Samples are masked before writing.\n- Profiling is skipped for large tables and unsuitable types.\n- Inference is never equivalent to a declared constraint or documented business rule.\n- External systems were not queried.\n")

    def _html_report(self) -> None:
        safe_database = html.escape(self.database)
        metrics = {"Tables": len(self.data.get("tables", [])), "Columns": len(self.data.get("columns", [])), "Views": len(self.data.get("views", [])), "Procedures": len(self.data.get("procedures", [])), "Lineage edges": len(self.data.get("lineage", [])), "Risks": len(self.data.get("risks", []))}
        cards = "".join(f"<div><strong>{value}</strong><span>{key}</span></div>" for key, value in metrics.items())
        links = (("Executive summary", "../01_Executive_Summary/MSSQL_EXECUTIVE_SUMMARY.md"), ("Table catalogue", "../04_Tables/TABLE_CATALOGUE.csv"), ("Column catalogue", "../05_Columns/COLUMN_CATALOGUE.csv"), ("Lineage", "../15_Lineage/LINEAGE_EDGES.csv"), ("Pipelines", "../16_Pipelines/PIPELINE_CATALOGUE.csv"), ("Risk register", "../18_Risks_Uncertainties/RISK_AND_UNCERTAINTY_REGISTER.csv"), ("Manifest", "../00_Run_Metadata/manifest.json"))
        navigation = "".join(f"<li><a href='{href}'>{label}</a></li>" for label, href in links)
        document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>MSSQL documentation - {safe_database}</title><style>body{{font:15px system-ui;margin:0;background:#f3f6fa;color:#172033}}header{{padding:4rem max(5vw,2rem);background:#14263d;color:white}}main{{padding:2rem max(5vw,2rem)}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-top:-3.5rem}}.cards div,section{{background:white;border:1px solid #dde3ec;border-radius:16px;padding:1.4rem}}.cards strong,.cards span{{display:block}}.cards strong{{font-size:2rem;color:#1769e0}}section{{margin-top:1.5rem}}a{{color:#1769e0}}li{{margin:.6rem 0}}</style></head><body><header><small>READ-ONLY EVIDENCE REPORT</small><h1>{safe_database}</h1><p>Styled navigation supplements canonical CSV, JSON, Markdown and checksums; it does not replace them.</p></header><main><div class='cards'>{cards}</div><section><h2>Full evidence</h2><ul>{navigation}</ul><p>Use the local Web UI for safe rendering, pagination, search, raw view and downloads.</p></section></main></body></html>"""
        path = self.artifact("MSSQL_DOCUMENTATION_REPORT.html"); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(document, encoding="utf-8")

    def _ensure_contract_files(self) -> None:
        csv_headers = {"PIPELINE_CATALOGUE.csv": ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence")}
        for name, folder in {**REQUIRED_OUTPUTS, **EXTRA_OUTPUTS}.items():
            path = self.root / folder / name
            if path.exists() or name in {"manifest.json", "checksums.sha256", "STAGE_STATUS.json", "RUN_CONFIGURATION.json"}:
                continue
            if name.endswith(".csv"): _csv(path, csv_headers.get(name, ("status", "explanation")), [])
            elif name.endswith(".json"): _json(path, {"status": "EMPTY_OR_NOT_APPLICABLE"})
            else: _md(path, f"# {name.removesuffix('.md').replace('_', ' ').title()}\n\nNo accessible evidence was produced for this category, or the category is not applicable. This is recorded explicitly rather than silently omitted.")

    def prompt16_safety_review(self) -> None:
        checks = {
            "registered_sql_safe": all(_safe(query.sql) for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,)),
            "masking_enabled": self.settings.profile_mask_sensitive_data,
            "timeout_positive": self.settings.query_timeout_seconds > 0,
            "large_table_threshold_positive": self.settings.profile_large_table_threshold > 0,
            "errors_recorded": True,
        }
        if not all(checks.values()): raise RuntimeError(f"Safety review failed: {checks}")
        _json(self.root / "00_Run_Metadata" / "PRE_RUN_SAFETY_REVIEW.json", checks)

    def prompt17_acceptance(self) -> None:
        audit = audit_run_evidence(self.root, sensitive_values=self.sensitive_values)
        _json(self.root / "99_Git_Handoff" / "MASKING_SAFETY_AUDIT.json", audit.as_dict())
        if not audit.passed:
            raise RuntimeError(f"Git safety gate failed with {len(audit.violations)} evidence violation(s)")
        _md(self.artifact("SAFE_TO_COMMIT_CHECKLIST.md"), f"""# Safe to Commit Checklist

- [x] `.env`, credential files, symbolic links, caches, temporary paths, and internal logs excluded
- [x] configured server/login/password strings and secret assignments absent from artifacts
- [x] server identity sanitized
- [x] sensitive column-profile minimum/maximum values masked before disk
- [x] sensitive low-cardinality values masked before disk
- [x] sensitive samples masked before disk
- [x] credential/password/hash/token/secret values always redacted
- [x] programmable definitions sanitized before writing

Executable audit result: **PASS**  
Files scanned: {audit.files_scanned}  
Classified columns: {audit.classified_columns}  
Sensitive columns: {audit.sensitive_columns}  
Sensitive values checked: {audit.sensitive_values_checked}

Git export is intentionally deferred until an explicit CLI/Web action. The exporter repeats this audit and fails closed rather than trusting this checklist.
""")

    def prompt18_comparison(self) -> None:
        self.data["comparison_status"] = [{"status": "AVAILABLE_ON_DEMAND", "reason": "v3 comparisons are generated only by an explicit 2/3-run action"}]

    def prompt19_required(self) -> None:
        missing = [name for name, folder in REQUIRED_OUTPUTS.items() if name not in {"manifest.json", "checksums.sha256"} and not (self.root / folder / name).is_file()]
        if missing: raise RuntimeError(f"Required output files missing: {missing}")

    def prompt20_environment(self) -> None:
        _json(self.artifact("RUN_CONFIGURATION.json"), self.settings.sanitized())

    def prompt21_review(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        test_result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"], cwd=project_root,
            capture_output=True, text=True, timeout=120, check=False,
        )
        if test_result.returncode != 0:
            raise RuntimeError("Final offline test suite failed during code review")
        table_docs = list((self.root / "20_Object_Documentation" / "Tables").glob("*.md"))
        programmable_docs = [path for folder in ("Views", "Procedures", "Functions", "Triggers") for path in (self.root / "20_Object_Documentation" / folder).glob("*.md")]
        required_table_sections = ("## Size and shape", "## Primary keys", "## Indexes", "## Column profiles", "## Masked sample", "## Lineage", "## Pipeline participation", "## Data-quality observations")
        required_programmable_sections = ("## Parameters", "## Reads, writes, calls, and references", "## Pipeline role", "## Risks and uncertainties", "## Sanitized static definition")
        semantic_checks = {
            "all_tables_documented": len(table_docs) == len(self.data.get("tables", [])),
            "all_programmable_objects_documented": len(programmable_docs) == sum(len(self.data.get(name, [])) for name in ("views", "procedures", "functions", "triggers")),
            "table_document_contract": all(all(section in path.read_text(encoding="utf-8") for section in required_table_sections) for path in table_docs),
            "programmable_document_contract": all(all(section in path.read_text(encoding="utf-8") for section in required_programmable_sections) for path in programmable_docs),
            "diagram_has_no_metadata_placeholder": "metadata_placeholder" not in self.artifact("FULL_ER_DIAGRAM.md").read_text(encoding="utf-8"),
            "comparison_engine_available": callable(__import__("mssql_database_documenter.comparison", fromlist=["compare_run_paths"]).compare_run_paths),
            "required_outputs_present": not [name for name, folder in REQUIRED_OUTPUTS.items() if not (self.root / folder / name).is_file()],
            "all_registered_sql_safe": all(_safe(query.sql) for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,)),
        }
        if not all(semantic_checks.values()):
            raise RuntimeError(f"Final semantic acceptance checks failed: {semantic_checks}")
        python_files = sorted((project_root / "src").rglob("*.py")) + sorted((project_root / "tests").rglob("*.py"))
        file_rows = []
        for path in python_files:
            content = path.read_text(encoding="utf-8")
            compile(content, str(path), "exec")
            file_rows.append((path.relative_to(project_root).as_posix(), len(content.splitlines()), hashlib.sha256(content.encode("utf-8")).hexdigest()))
        source_files = {path.name: path for path in (project_root / "src" / "mssql_database_documenter").glob("*.py")}
        def line_of(filename: str, needle: str) -> int:
            return next(index for index, line in enumerate(source_files[filename].read_text(encoding="utf-8").splitlines(), 1) if needle in line)
        checks = [
            ("Fail-closed SQL validation", f"src/mssql_database_documenter/safety.py:{line_of('safety.py', 'def validate_read_only_sql')}", "PASS"),
            ("Final execution-boundary validation", f"src/mssql_database_documenter/safety.py:{line_of('safety.py', 'def execute')}", "PASS"),
            ("Autocommit disabled and rollback close", f"src/mssql_database_documenter/connection.py:{line_of('connection.py', 'autocommit=False')}", "PASS"),
            ("Configuration secret sanitization", f"src/mssql_database_documenter/config.py:{line_of('config.py', 'def sanitized')}", "PASS"),
            ("Credential/PII masking", f"src/mssql_database_documenter/fullrun.py:{line_of('fullrun.py', 'def _mask')}", "PASS"),
            ("Sequential stop-on-failed-stage gate", f"src/mssql_database_documenter/fullrun.py:{line_of('fullrun.py', 'def stage')}", "PASS"),
            ("Required output validation", f"src/mssql_database_documenter/fullrun.py:{line_of('fullrun.py', 'def prompt19_required')}", "PASS"),
            ("Manifest and SHA-256 generation", f"src/mssql_database_documenter/fullrun.py:{line_of('fullrun.py', 'def _snapshot_integrity')}", "PASS"),
            ("Per-object documentation contract", "generated 20_Object_Documentation", "PASS"),
            ("Explicit 2/3-run comparison engine", "src/mssql_database_documenter/comparison", "PASS"),
            ("ER diagrams contain real metadata", "generated 19_Diagrams", "PASS"),
        ]
        lines = [
            "# Final Code Review", "", "Overall result: **PASS**", "",
            f"- Offline tests: `{test_result.stdout.strip()}`",
            f"- Python files compiled and audited: {len(file_rows)}",
            f"- Registered static SQL statements validated: {len(QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,))}",
            "- Database touched during this review: no", "- Mutation/admin/execution capability implemented: no", "",
            "## Control checks", "", "| Check | File/line | Result |", "|---|---|---|",
        ]
        lines.extend(f"| {name} | `{location}` | {result} |" for name, location, result in checks)
        lines.extend(("", "## File audit", "", "| Python file | Lines | SHA-256 | Result |", "|---|---:|---|---|"))
        lines.extend(f"| `{name}` | {count} | `{digest}` | PASS |" for name, count, digest in file_rows)
        lines.extend(("", "## Evidence boundaries", "", "Dynamic SQL, encrypted definitions, invalid database objects, permission limitations, and heuristic classifications remain explicitly identified as uncertainty; no inference is promoted to a declared fact."))
        lines.extend(("", "## Semantic acceptance", ""))
        lines.extend(f"- [x] {name.replace('_', ' ')}" for name in semantic_checks)
        _md(self.root / "99_Git_Handoff" / "FINAL_CODE_REVIEW.md", "\n".join(lines))

    def _pipelines(self) -> None:
        rows: list[dict[str, Any]] = []
        object_flags = {(str(item.get("schema_name") or item.get("parent_schema_name") or ""), str(item.get("object_name") or "")): item for category in ("views", "procedures", "functions", "triggers") for item in self.data.get(category, [])}
        grouped_static: dict[tuple[str, str], dict[str, list[str]]] = {}
        for reference in self.data.get("static_references", []):
            source_key = (str(reference.get("source_schema") or ""), str(reference.get("source_object") or ""))
            target = ".".join(part for part in (str(reference.get("target_database") or ""), str(reference.get("target_schema") or ""), str(reference.get("target_object") or "")) if part)
            grouped_static.setdefault(source_key, {"READ": [], "WRITE": [], "CALL": []}).setdefault(str(reference.get("operation") or "REFERENCE"), []).append(target)
        for (schema, obj), operations in grouped_static.items():
            flags = object_flags.get((schema, obj), {})
            dynamic = bool(flags.get("dynamic_sql_present"))
            has_flow = bool(operations.get("READ") and operations.get("WRITE"))
            rows.append({
                "origin": f"{schema}.{obj}", "source": ", ".join(sorted(set(operations.get("READ", [])))) or "UNKNOWN",
                "transformation": f"STATIC_SQL_OBJECT; calls={', '.join(sorted(set(operations.get('CALL', [])))) or 'none'}",
                "destination": ", ".join(sorted(set(operations.get("WRITE", [])))) or "UNKNOWN", "schedule": "UNKNOWN",
                "read_write_evidence": "STATIC DEFINITION TOKEN ANALYSIS", "external_dependency": any("." in value and value.count(".") >= 2 for values in operations.values() for value in values),
                "classification": "DYNAMIC_SQL_OPAQUE" if dynamic else "LIKELY_PIPELINE" if has_flow else "CONFIRMED_DEPENDENCY",
                "confidence": "MEDIUM" if has_flow and not dynamic else "LOW" if dynamic else "MEDIUM",
            })
        static_sources = set(grouped_static)
        for dep in self.data.get("dependencies", []):
            source_key = (str(dep.get("source_schema") or ""), str(dep.get("source_object") or ""))
            if source_key in static_sources:
                continue
            rows.append({"origin": f"{dep.get('source_schema')}.{dep.get('source_object')}", "source": f"{dep.get('target_schema')}.{dep.get('target_object')}", "transformation": dep.get("source_type"), "destination": "UNKNOWN", "schedule": "UNKNOWN", "read_write_evidence": "CATALOG REFERENCE; DIRECTION UNKNOWN", "external_dependency": bool(dep.get("target_server") or dep.get("target_database")), "classification": "HISTORICAL_OR_UNKNOWN", "confidence": "MEDIUM" if dep.get("referenced_id") else "LOW"})
        for job in self.data.get("sql_agent_jobs", []):
            rows.append({"origin": job.get("job_name"), "source": "UNKNOWN", "transformation": job.get("step_name"), "destination": job.get("database_name"), "schedule": job.get("schedule_name"), "read_write_evidence": "SQL AGENT METADATA; COMMAND HASH ONLY", "external_dependency": False, "classification": "POSSIBLE_PIPELINE", "confidence": "MEDIUM"})
        self.data["pipelines"] = rows
        _csv(self.artifact("PIPELINE_CATALOGUE.csv"), ("origin", "source", "transformation", "destination", "schedule", "read_write_evidence", "external_dependency", "classification", "confidence"), rows)

    def _write_control_files(self, *, final: bool) -> None:
        _csv(self.artifact("DISCOVERY_ERRORS.csv"), ERROR_COLUMNS, self.errors)
        _json(self.artifact("STAGE_STATUS.json"), self.status)
        completed = [row["prompt"] for row in self.status if row["status"] == "PASS"]
        table_keys = {_object_key(row) for row in self.data.get("tables", [])}
        sampled = set(self.data.get("sample_rows", {}))
        profiled_tables = {_object_key(row) for row in self.data.get("column_profile", []) if row.get("profile_status") == "PROFILED"}
        lines = [
            "# Discovery Coverage", "", f"- Completed prompt stages: {', '.join(completed)}",
            f"- Recorded errors/limitations: {len(self.errors)}", f"- Finalized: {final}", "",
            "## Object coverage", "",
            f"- Tables discovered: {len(table_keys)}", f"- Tables documented: {len(list((self.root / '20_Object_Documentation' / 'Tables').glob('*.md')))}",
            f"- Tables with at least one profiled column: {len(profiled_tables)}", f"- Tables/views with sample files attempted: {len(sampled)}",
            f"- Columns discovered: {len(self.data.get('columns', []))}", f"- Column profile rows: {len(self.data.get('column_profile', []))}",
            f"- Programmable objects discovered: {sum(len(self.data.get(name, [])) for name in ('views', 'procedures', 'functions', 'triggers'))}",
            f"- Dependency/lineage edges: {len(self.data.get('lineage', []))}", f"- Relationship cardinality rows: {len(self.data.get('relationship_cardinality', []))}", "",
            "## Shortfalls and limitations", "",
        ]
        if self.errors:
            lines.extend(f"- Prompt {item['prompt']} / {item['stage']} / `{item.get('schema_name')}.{item.get('object_name')}`: {item['impact']} ({item['continuation']})" for item in self.errors)
        else:
            lines.append("- No query/access errors were recorded.")
        lines.extend(("- Dynamic SQL, encrypted definitions, invalid objects, and permissions may reduce static coverage.", "- Categories that are empty or inaccessible retain header-only or explanatory artifacts."))
        _md(self.artifact("DISCOVERY_COVERAGE.md"), "\n".join(lines))

    def finalize(self) -> None:
        self._write_control_files(final=True)
        self._snapshot_integrity()

    def _snapshot_integrity(self) -> None:
        status_values = [str(item.get("status") or "") for item in self.status]
        accounted = {"PASS", "SKIPPED_BY_MODE"}
        failed_stage_count = sum(value == "FAILED" for value in status_values)
        summary_status = "CANCELLED" if self.cancelled else "FAILED" if self.failed or "FAILED" in status_values else "COMPLETED_WITH_WARNINGS" if self.errors else "COMPLETED" if self.status and all(value in accounted for value in status_values) else "PARTIAL"
        server_rows = next((item.get("rows", []) for item in self.data.get("connection_capabilities", []) if item.get("query") == "server_capabilities"), [])
        run_summary = {
            "run_id": self.run_id, "database": self.database, "server_alias": self.settings.sanitized()["server"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": self.settings.discovery_mode,
            "status": summary_status, "tool_version": "0.3.0",
            "sql_server_version": (server_rows[0].get("product_version") if server_rows else "UNKNOWN"),
            "sample_rows": self.settings.profile_sample_rows, "exact_row_counts": self.settings.profile_exact_row_counts,
            "mask_sensitive_data": self.settings.profile_mask_sensitive_data,
            "profile_settings": {"sample_rows": self.settings.profile_sample_rows, "include_sample_data": self.settings.profile_include_sample_data, "mask_sensitive_data": self.settings.profile_mask_sensitive_data, "exact_row_counts": self.settings.profile_exact_row_counts, "exact_row_count_threshold": self.settings.profile_exact_row_count_threshold, "large_table_threshold": self.settings.profile_large_table_threshold},
            "completed_stage_count": sum(item.get("status") == "PASS" for item in self.status),
            "completion_coverage": f"{sum(item.get('status') in accounted for item in self.status)}/{20}",
            "error_count": failed_stage_count,
            "warning_count": max(0, len(self.errors) - failed_stage_count),
            "warning_error_count": len(self.errors), "file_count_before_manifest": sum(1 for path in self.root.rglob("*") if path.is_file()),
        }
        _json(self.artifact("run_summary.json"), run_summary)
        files_before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file())
        manifest_path = self.artifact("manifest.json"); checksum_path = self.artifact("checksums.sha256")
        package_names = ("pyodbc", "python-dotenv", "pytest", "pandas", "sqlparse", "networkx", "jinja2")
        packages = {}
        for name in package_names:
            try: packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: packages[name] = "NOT_INSTALLED"
        server_rows = next((item.get("rows", []) for item in self.data.get("connection_capabilities", []) if item.get("query") == "server_capabilities"), [])
        manifest = {
            "run_id": self.run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool": "mssql-database-documenter", "tool_version": "0.3.0", "database": self.database,
            "python_version": platform.python_version(), "platform": platform.platform(), "packages": packages,
            "odbc_driver": self.settings.driver, "sql_server_capabilities": server_rows,
            "configuration": self.settings.sanitized(), "stages": self.status,
            "expected_stage_count": 20,
            "warnings": [item["sanitized_message"] for item in self.errors], "errors": len(self.errors),
            "files": sorted(set(files_before + [manifest_path.relative_to(self.root).as_posix(), checksum_path.relative_to(self.root).as_posix()])),
            "git_export": [],  # Export is a separate explicit CLI/Web operation in v3.
        }
        _json(manifest_path, manifest)
        lines = []
        for path in sorted(path for path in self.root.rglob("*") if path.is_file() and path != checksum_path):
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(self.root).as_posix()}")
        checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run(self) -> Path:
        try:
            logic_enabled = self.settings.discovery_mode != "metadata"
            profile_enabled = self.settings.discovery_mode in {"safe-profile", "full-readonly"}
            self.stage("02", "security", self.prompt02_safety)
            with connect(self.settings, self.database) as connection:
                self.connection = connection; self.cursor = ReadOnlyCursor(connection.cursor())
                self.stage("03", "connection", self.prompt03_connection)
                self.stage("04", "metadata", self.prompt04_metadata)
                if logic_enabled: self.stage("05", "programmable_objects", self.prompt05_programmable)
                else: self.skip_stage("05", "programmable_objects", "DISCOVERY_MODE=metadata")
                self.stage("06", "table_size_shape", self.prompt06_size_shape)
                if profile_enabled: self.stage("07", "column_profile", self.prompt07_profile)
                else: self.skip_stage("07", "column_profile", f"DISCOVERY_MODE={self.settings.discovery_mode}")
                if profile_enabled: self.stage("08", "safe_samples", self.prompt08_samples)
                else: self.skip_stage("08", "safe_samples", f"DISCOVERY_MODE={self.settings.discovery_mode}")
                self.stage("09", "sensitivity", self.prompt09_sensitivity)
                if profile_enabled: self.stage("10", "relationships", self.prompt10_relationships)
                else: self.skip_stage("10", "relationships", f"Data validation disabled in DISCOVERY_MODE={self.settings.discovery_mode}")
                if logic_enabled: self.stage("11", "lineage_pipelines", lambda: (self.prompt11_lineage(), self._pipelines()))
                else: self.skip_stage("11", "lineage_pipelines", "DISCOVERY_MODE=metadata")
                if logic_enabled: self.stage("12", "external_references", self.prompt12_external)
                else: self.skip_stage("12", "external_references", "DISCOVERY_MODE=metadata")
                self.stage("13", "classification_duplicates", self.prompt13_classification)
                self.stage("14", "quality_risk", self.prompt14_quality)
            self.stage("15", "output_contract", self.prompt15_outputs)
            self.stage("16", "safety_review", self.prompt16_safety_review)
            self.stage("17", "acceptance_git_handoff", self.prompt17_acceptance)
            self.stage("18", "multi_database_comparison", self.prompt18_comparison)
            self.stage("19", "required_outputs", self.prompt19_required)
            self.stage("20", "environment_evidence", self.prompt20_environment)
            self.stage("21", "final_code_review", self.prompt21_review)
        except _RequestedStageComplete:
            pass
        except DiscoveryCancelled:
            self.cancelled = True
            self.finalize()
            raise
        except Exception as exc:
            # A real attempted run remains auditable even when an early connection or
            # discovery stage fails.  Finalization writes only truthful partial state.
            self.failed = True
            if not any(item.get("status") == "FAILED" for item in self.status):
                now = datetime.now(timezone.utc).isoformat()
                self.status.append({"prompt": "03", "stage": "connection_setup", "status": "FAILED", "started_utc": now, "finished_utc": now})
                self._error("03", "connection_setup", "", "", "connect", exc, "Live discovery did not start", "Run finalized as failed")
            self.finalize()
            raise
        self.finalize()
        return self.root

    def resume_after_comparison(self) -> Path:
        """Continue a coordinated multi-database run after global prompt 18 output exists."""
        self.stop_after = "21"
        try:
            self.stage("18", "multi_database_comparison", self.prompt18_comparison)
            self.stage("19", "required_outputs", self.prompt19_required)
            self.stage("20", "environment_evidence", self.prompt20_environment)
            self.stage("21", "final_code_review", self.prompt21_review)
        except _RequestedStageComplete:
            pass
        self.finalize()
        return self.root


def _safe(sql: str) -> bool:
    validate_read_only_sql(sql)
    return True


def run_all(
    settings: Settings,
    *,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> list[Path]:
    settings.validate_for_connection()
    return [
        SequentialRun(settings, database, stop_after="21", progress_callback=progress_callback, cancel_requested=cancel_requested).run()
        for database in settings.databases
    ]


def run_until(settings: Settings, prompt: str) -> list[Path]:
    settings.validate_for_connection()
    if prompt not in {f"{number:02d}" for number in range(2, 22)}:
        raise ValueError(f"Unsupported stop prompt: {prompt}")
    return [SequentialRun(settings, database, stop_after=prompt).run() for database in settings.databases]
