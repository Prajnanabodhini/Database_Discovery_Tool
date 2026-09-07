"""Shared run-engine primitives with no domain-stage ownership."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .safety import validate_read_only_sql


ERROR_COLUMNS = (
    "prompt", "stage", "database", "schema_name", "object_name", "query_name",
    "error_type", "sanitized_message", "impact", "continuation",
)


def markdown_table(rows: Iterable[dict[str, Any]], columns: tuple[str, ...]) -> list[str]:
    values = list(rows)
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in values:
        cells = [str(row.get(column, "")).replace("|", "\\|").replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    if not values:
        lines.append("| " + " | ".join("None observed" if index == 0 else "" for index, _ in enumerate(columns)) + " |")
    return lines


def write_csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    headers = list(columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def quote_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("Invalid SQL identifier from metadata")
    return "[" + value.replace("]", "]]" ) + "]"


def object_key(row: dict[str, Any], schema_key: str = "schema_name", object_key: str = "object_name") -> str:
    return f"{row.get(schema_key) or ''}.{row.get(object_key) or ''}"


def is_access_limitation(exc: Exception) -> bool:
    message = str(exc).casefold()
    return any(
        marker in message
        for marker in (
            "permission was denied", "select permission denied", "not authorized",
            "does not have permission", "user does not have permission", "access is denied",
            "insufficient permission", "view database state permission",
            "cannot open database", "login failed", "binding errors",
            "could not use view or function", "definition is encrypted",
        )
    )


def sql_is_safe(sql: str) -> bool:
    try:
        validate_read_only_sql(sql)
        return True
    except Exception:
        return False
