"""Column/table profiling policy helpers."""

from __future__ import annotations

from typing import Any

from .sensitivity import classify_sensitivity, mask_value


SKIP_PROFILE_TYPES = frozenset(
    {"binary", "varbinary", "image", "text", "ntext", "xml", "sql_variant", "timestamp", "rowversion", "hierarchyid", "geography", "geometry"}
)
STRING_TYPES = frozenset({"char", "varchar", "nchar", "nvarchar"})
NUMERIC_TYPES = frozenset({"tinyint", "smallint", "int", "bigint", "decimal", "numeric", "money", "smallmoney", "float", "real"})
DATE_TYPES = frozenset({"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset", "time"})


def type_family(data_type: str) -> str:
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


def classification(column_name: str) -> tuple[str, str]:
    result = classify_sensitivity(column_name)
    return result.category, result.action


def mask(value: Any, category: str, salt: str, masking_enabled: bool = True) -> Any:
    return mask_value(value, category, salt, masking_enabled)
