"""Static, non-executing analysis of SQL Agent step commands.

Raw command text is transient input. Only hashes, conservative references, and
non-sensitive classifications may leave this module. No execution API is used.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from typing import Any

from ..redaction import redact_text


RAW_COMMAND_FIELD = "command_text_internal"

_IDENTIFIER = r"(?:\[[^\]]*(?:\]\][^\]]*)*\]|[A-Za-z_#][A-Za-z0-9_$#@]*)"
_QUALIFIED_NAME = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER}){{0,3}}"
_REFERENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("WRITE", re.compile(rf"\bINSERT\s+(?:INTO\s+)?(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
    ("WRITE", re.compile(rf"\bMERGE\s+(?:INTO\s+)?(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
    ("WRITE", re.compile(rf"\bUPDATE\s+(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
    ("WRITE", re.compile(rf"\bDELETE\s+FROM\s+(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
    ("READ", re.compile(rf"\b(?:FROM|JOIN)\s+(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
    ("CALL", re.compile(rf"\bEXEC(?:UTE)?\s+(?P<name>{_QUALIFIED_NAME})", re.IGNORECASE)),
)
_DYNAMIC_SQL = re.compile(
    r"\bsp_executesql\b|\bEXEC(?:UTE)?\s*\(|\bEXEC(?:UTE)?\s+@[A-Za-z_]",
    re.IGNORECASE,
)
_EXTERNAL_SQL_CONSTRUCT = re.compile(r"\b(OPENQUERY|OPENROWSET|OPENDATASOURCE)\s*\(", re.IGNORECASE)
_SECRET_ARGUMENT = re.compile(
    r"(?ix)"
    r"(?P<label>(?:--?|/)?(?:password|passwd|pwd|token|secret|api[-_]?key|access[-_]?key))"
    r"(?P<separator>\s*(?:=|:|\s)\s*)"
    r"(?P<value>'[^']*'|\"[^\"]*\"|[^\s;]+)",
)
_SECRET_WORD = re.compile(
    r"\b(?:password|passwd|pwd|token|secret|api[-_]?key|access[-_]?key)\b",
    re.IGNORECASE,
)
_NON_TSQL_HINTS = {
    "POWERSHELL": ("PowerShell invocation; command and arguments redacted", "POWERSHELL_OPAQUE"),
    "CMDEXEC": ("CmdExec invocation; command and arguments redacted", "CMDEXEC_OPAQUE"),
    "SSIS": ("SSIS package invocation; location and arguments redacted", "SSIS_OPAQUE"),
}


def _string(value: Any) -> str:
    return "" if value is None else str(value)


def _safe_metadata(value: Any, sensitive_values: Iterable[str]) -> str:
    return redact_text(_string(value), sensitive_values=sensitive_values)


def _command_sha(command: str, supplied: Any) -> str:
    supplied_text = _string(supplied).strip()
    if supplied_text:
        return supplied_text.upper()
    return hashlib.sha256(command.encode("utf-8", errors="replace")).hexdigest().upper()


def _sanitize_command(command: str, sensitive_values: Iterable[str]) -> str:
    sanitized = redact_text(command, sensitive_values=sensitive_values)
    return _SECRET_ARGUMENT.sub(lambda match: f"{match.group('label')}=[REDACTED]", sanitized)


def _scrub_literals_and_comments(command: str) -> str:
    """Replace comments and string literals with spaces while preserving offsets."""
    result = list(command)
    index = 0
    state = "code"
    while index < len(command):
        char = command[index]
        following = command[index + 1] if index + 1 < len(command) else ""
        if state == "code" and char == "'":
            result[index] = " "
            state = "string"
        elif state == "code" and char == "-" and following == "-":
            result[index] = result[index + 1] = " "
            index += 1
            state = "line_comment"
        elif state == "code" and char == "/" and following == "*":
            result[index] = result[index + 1] = " "
            index += 1
            state = "block_comment"
        elif state == "string":
            result[index] = " "
            if char == "'" and following == "'":
                result[index + 1] = " "
                index += 1
            elif char == "'":
                state = "code"
        elif state == "line_comment":
            if char in "\r\n":
                state = "code"
            else:
                result[index] = " "
        elif state == "block_comment":
            result[index] = " "
            if char == "*" and following == "/":
                result[index + 1] = " "
                index += 1
                state = "code"
        index += 1
    return "".join(result)


def _is_dynamic_sql(scrubbed: str) -> bool:
    if _DYNAMIC_SQL.search(scrubbed):
        return True
    return bool(re.search(r"\bEXEC(?:UTE)?\b[^;]*\+", scrubbed, re.IGNORECASE))


def _provably_safe_tsql(command: str, sanitized: str, dynamic_sql: bool) -> bool:
    if not command or command != sanitized or len(command) > 4000 or dynamic_sql:
        return False
    if any(character in command for character in ("'", '"')):
        return False
    if "--" in command or "/*" in command or "*/" in command:
        return False
    if _SECRET_WORD.search(command):
        return False
    return not any(ord(character) < 32 and character not in "\r\n\t" for character in command)


def _identifier_parts(name: str) -> list[str]:
    parts = re.findall(_IDENTIFIER, name)
    return [part[1:-1].replace("]]", "]") if part.startswith("[") else part for part in parts]


def _target_details(
    name: str,
    source_database: str,
    sensitive_values: Iterable[str],
) -> dict[str, Any]:
    parts = [_safe_metadata(part, sensitive_values) for part in _identifier_parts(name)]
    server = ""
    database = source_database
    schema = ""
    object_name = ""
    reference_kind = "UNQUALIFIED"
    external = False
    if len(parts) == 4:
        server_hash = hashlib.sha256(parts[0].encode("utf-8", errors="replace")).hexdigest()[:12].upper()
        server = f"[EXTERNAL_SERVER:{server_hash}]"
        database, schema, object_name = parts[1:]
        reference_kind = "FOUR_PART"
        external = True
    elif len(parts) == 3:
        database, schema, object_name = parts
        reference_kind = "THREE_PART"
        external = not source_database or database.casefold() != source_database.casefold()
    elif len(parts) == 2:
        schema, object_name = parts
        reference_kind = "TWO_PART"
    elif parts:
        object_name = parts[0]
    return {
        "target_server": server,
        "target_database": database,
        "target_schema": schema,
        "target_object": object_name,
        "reference_kind": reference_kind,
        "external_reference": external,
    }


def _base_reference(public_row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "job_name": public_row.get("job_name", ""),
        "step_id": public_row.get("step_id", ""),
        "step_name": public_row.get("step_name", ""),
        "subsystem": public_row.get("subsystem", ""),
        "source_database": public_row.get("database_name", ""),
    }


def _tsql_references(
    command: str,
    public_row: Mapping[str, Any],
    sensitive_values: Iterable[str],
) -> tuple[list[dict[str, Any]], bool]:
    scrubbed = _scrub_literals_and_comments(command)
    dynamic_sql = _is_dynamic_sql(scrubbed)
    references: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for operation, pattern in _REFERENCE_PATTERNS:
        for match in pattern.finditer(scrubbed):
            name = match.group("name")
            if operation == "READ" and name.casefold() in {"openquery", "openrowset", "opendatasource"}:
                continue
            if operation == "CALL" and name.casefold().rstrip(";") in {
                "sp_executesql",
                "sys.sp_executesql",
            }:
                continue
            target = _target_details(name, _string(public_row.get("database_name")), sensitive_values)
            identity = (
                operation,
                _string(target["target_server"]).casefold(),
                _string(target["target_database"]).casefold(),
                _string(target["target_schema"]).casefold(),
                _string(target["target_object"]).casefold(),
            )
            if identity in seen:
                continue
            seen.add(identity)
            references.append(
                {
                    **_base_reference(public_row),
                    "operation": operation,
                    **target,
                    "dynamic_sql_opaque": dynamic_sql,
                    "evidence": "STATIC TSQL TOKEN REFERENCE; NEVER EXECUTED",
                    "evidence_class": "INFERENCE",
                    "confidence": "LOW" if target["reference_kind"] == "UNQUALIFIED" else "MEDIUM",
                }
            )
    for match in _EXTERNAL_SQL_CONSTRUCT.finditer(scrubbed):
        construct = match.group(1).upper()
        references.append(
            {
                **_base_reference(public_row),
                "operation": "READ",
                "target_server": "[STATIC_TEXT_REDACTED]",
                "target_database": "",
                "target_schema": "",
                "target_object": "",
                "reference_kind": construct,
                "external_reference": True,
                "dynamic_sql_opaque": dynamic_sql,
                "evidence": f"{construct} STATIC INVOCATION DETECTED; ARGUMENTS OPAQUE; NEVER EXECUTED",
                "evidence_class": "INFERENCE",
                "confidence": "LOW",
            }
        )
    if dynamic_sql:
        references.append(
            {
                **_base_reference(public_row),
                "operation": "OPAQUE",
                "target_server": "",
                "target_database": "",
                "target_schema": "",
                "target_object": "",
                "reference_kind": "DYNAMIC_SQL",
                "external_reference": False,
                "dynamic_sql_opaque": True,
                "evidence": "DYNAMIC SQL DETECTED; TEXT NOT INTERPRETED OR EXECUTED",
                "evidence_class": "INFERENCE",
                "confidence": "LOW",
            }
        )
    return references, dynamic_sql


def _opaque_reference(public_row: Mapping[str, Any], classification: str) -> dict[str, Any]:
    subsystem = _string(public_row.get("subsystem")).upper()
    return {
        **_base_reference(public_row),
        "operation": "OPAQUE",
        "target_server": "",
        "target_database": "",
        "target_schema": "",
        "target_object": "",
        "reference_kind": "SSIS_PACKAGE" if subsystem == "SSIS" else "EXTERNAL_INVOCATION",
        "external_reference": True,
        "dynamic_sql_opaque": False,
        "evidence": f"{classification}; COMMAND AND ARGUMENTS REDACTED; NEVER EXECUTED",
        "evidence_class": "INFERENCE",
        "confidence": "LOW",
    }


def _target_label(reference: Mapping[str, Any]) -> str:
    parts = [
        _string(reference.get("target_server")),
        _string(reference.get("target_database")),
        _string(reference.get("target_schema")),
        _string(reference.get("target_object")),
    ]
    return ".".join(part for part in parts if part) or "UNKNOWN"


def _pipeline_edge(reference: Mapping[str, Any], public_row: Mapping[str, Any]) -> dict[str, Any]:
    operation = _string(reference.get("operation")).upper()
    target = _target_label(reference)
    source = target if operation == "READ" else "UNKNOWN"
    destination = target if operation == "WRITE" else "UNKNOWN"
    transformation = _string(public_row.get("step_name")) or "UNKNOWN"
    if operation == "CALL":
        transformation = f"CALL {target}"
    elif operation == "OPAQUE":
        transformation = _string(public_row.get("invocation_hint")) or "OPAQUE STEP"
    return {
        "job_name": public_row.get("job_name", ""),
        "step_id": public_row.get("step_id", ""),
        "step_name": public_row.get("step_name", ""),
        "subsystem": public_row.get("subsystem", ""),
        "origin": f"SQL Agent job: {public_row.get('job_name', '')}",
        "source": source,
        "transformation": transformation,
        "destination": destination,
        "schedule": public_row.get("schedule_name", "") or "UNKNOWN",
        "operation": operation,
        "read_write_evidence": reference.get("evidence", ""),
        "external_dependency": reference.get("external_reference", False),
        "classification": "OPAQUE_EXTERNAL_STEP" if operation == "OPAQUE" else "POSSIBLE_PIPELINE",
        "confidence": reference.get("confidence", "LOW"),
        "evidence_class": reference.get("evidence_class", "INFERENCE"),
        "reference_kind": reference.get("reference_kind", ""),
        "dynamic_sql_opaque": reference.get("dynamic_sql_opaque", False),
    }


def analyze_agent_steps(
    rows: Iterable[Mapping[str, Any]],
    *,
    sensitive_values: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return persistable job rows, static references, and pipeline edges."""
    sensitive = tuple(value for value in sensitive_values if value)
    public_jobs: list[dict[str, Any]] = []
    all_references: list[dict[str, Any]] = []
    pipeline_edges: list[dict[str, Any]] = []
    for row in rows:
        command = _string(row.get(RAW_COMMAND_FIELD))
        public: dict[str, Any] = {key: value for key, value in row.items() if key != RAW_COMMAND_FIELD}
        for key in ("job_name", "description", "step_name", "subsystem", "database_name", "schedule_name"):
            if key in public:
                public[key] = _safe_metadata(public[key], sensitive)
        subsystem = _string(public.get("subsystem")).strip().upper()
        public["subsystem"] = subsystem
        public["command_sha256"] = _command_sha(command, public.get("command_sha256"))
        sanitized = _sanitize_command(command, sensitive)
        if subsystem == "TSQL":
            references, dynamic_sql = _tsql_references(command, public, sensitive)
            safe_command = _provably_safe_tsql(command, sanitized, dynamic_sql)
            public["command_text_sanitized"] = sanitized if safe_command else ""
            public["invocation_hint"] = "dynamic TSQL; text treated as opaque" if dynamic_sql else "static TSQL parsed without execution"
            public["command_classification"] = "DYNAMIC_TSQL_OPAQUE" if dynamic_sql else "STATIC_TSQL"
            public["dynamic_sql_opaque"] = dynamic_sql
        else:
            hint, classification = _NON_TSQL_HINTS.get(
                subsystem,
                (f"{subsystem or 'External'} invocation; command and arguments redacted", "EXTERNAL_OPAQUE"),
            )
            public["command_text_sanitized"] = ""
            public["invocation_hint"] = hint
            public["command_classification"] = classification
            public["dynamic_sql_opaque"] = False
            references = [_opaque_reference(public, classification)]
        public_jobs.append(public)
        all_references.extend(references)
        pipeline_edges.extend(_pipeline_edge(reference, public) for reference in references)
    return public_jobs, all_references, pipeline_edges


SQL_AGENT_REFERENCE_HEADERS = (
    "job_name", "step_id", "step_name", "subsystem", "source_database", "operation",
    "target_server", "target_database", "target_schema", "target_object", "reference_kind",
    "external_reference", "dynamic_sql_opaque", "evidence", "evidence_class", "confidence",
)

SQL_AGENT_PIPELINE_HEADERS = (
    "job_name", "step_id", "step_name", "subsystem", "origin", "source", "transformation",
    "destination", "schedule", "operation", "read_write_evidence", "external_dependency",
    "classification", "confidence", "evidence_class", "reference_kind", "dynamic_sql_opaque",
)
