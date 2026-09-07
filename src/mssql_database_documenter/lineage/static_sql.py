"""Conservative static SQL definition and lineage helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from ..redaction import redact_text


def sanitized_external_server(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"[EXTERNAL_SERVER:{digest}]"


def definition_references(row: dict[str, Any]) -> list[dict[str, str]]:
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


def static_column_references(
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


def static_definition(row: dict[str, Any]) -> dict[str, Any]:
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
