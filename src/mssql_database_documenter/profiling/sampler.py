"""Bounded table/view sampling plans and pre-persistence masking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from .sensitivity import SENSITIVE_CATEGORIES, SensitivityResult, mask_value


TABLE_TYPES = frozenset({"TABLE", "USER_TABLE"})
VIEW_TYPES = frozenset({"VIEW"})


def quote_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("Invalid SQL identifier from metadata")
    return "[" + value.replace("]", "]]" ) + "]"


def _truthy(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return bool(value)


def _integer(value: object) -> int | None:
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


@dataclass(frozen=True, slots=True)
class SamplePlan:
    schema_name: str
    object_name: str
    object_type: str
    requested_rows: int
    ordering_strategy: str
    sql: str
    enabled: bool = True
    status: str = "READY"


@dataclass(frozen=True, slots=True)
class SanitizedSample:
    rows: tuple[dict[str, object], ...]
    classifications: Mapping[str, SensitivityResult]
    masked_sensitive_column_count: int


def _primary_key_order(primary_keys: Iterable[Mapping[str, object]]) -> tuple[str, ...]:
    rows = sorted(primary_keys, key=lambda row: int(row.get("key_ordinal") or 0))
    return tuple(str(row.get("column_name") or "") for row in rows if int(row.get("key_ordinal") or 0) > 0 and row.get("column_name"))


def _unique_index_order(indexes: Iterable[Mapping[str, object]]) -> tuple[str, ...]:
    groups: dict[tuple[int, str], list[Mapping[str, object]]] = {}
    for row in indexes:
        ordinal = int(row.get("key_ordinal") or 0)
        if (
            not _truthy(row.get("is_unique"))
            or _truthy(row.get("is_disabled"))
            or _truthy(row.get("has_filter"))
            or _truthy(row.get("is_included_column"))
            or ordinal <= 0
            or not row.get("column_name")
        ):
            continue
        index_id = _integer(row.get("index_id")) or 0
        groups.setdefault((index_id, str(row.get("index_name") or "")), []).append(row)
    if not groups:
        return ()
    _, selected = min(groups.items(), key=lambda item: (item[0][0], item[0][1].casefold()))
    ordered = sorted(selected, key=lambda row: int(row.get("key_ordinal") or 0))
    return tuple(str(row["column_name"]) for row in ordered)


def build_sample_plan(
    *,
    schema_name: str,
    object_name: str,
    object_type: str,
    requested_rows: int,
    sample_tables: bool,
    sample_views: bool,
    sample_large_tables: bool,
    estimated_rows: int | None,
    profile_large_table_threshold: int,
    primary_keys: Iterable[Mapping[str, object]] = (),
    indexes: Iterable[Mapping[str, object]] = (),
) -> SamplePlan:
    """Plan one bounded SELECT without counting rows or introducing random scans."""
    if requested_rows < 1:
        raise ValueError("Sample row limit must be positive")
    normalized_type = object_type.strip().upper()
    if normalized_type in TABLE_TYPES:
        if not sample_tables:
            return SamplePlan(schema_name, object_name, normalized_type, requested_rows, "NOT_APPLICABLE", "", False, "SKIPPED_TABLE_SAMPLING_DISABLED")
        if estimated_rows is not None and estimated_rows > profile_large_table_threshold and not sample_large_tables:
            return SamplePlan(schema_name, object_name, normalized_type, requested_rows, "NOT_APPLICABLE", "", False, "SKIPPED_LARGE_TABLE_SAMPLING_DISABLED")
        order_columns = _primary_key_order(primary_keys)
        strategy = "PRIMARY_KEY" if order_columns else ""
        if not order_columns:
            order_columns = _unique_index_order(indexes)
            strategy = "UNIQUE_INDEX" if order_columns else "UNORDERED_TOP"
    elif normalized_type in VIEW_TYPES:
        if not sample_views:
            return SamplePlan(schema_name, object_name, normalized_type, requested_rows, "NOT_APPLICABLE", "", False, "SKIPPED_VIEW_SAMPLING_DISABLED")
        order_columns = ()
        strategy = "UNORDERED_TOP_VIEW"
    else:
        return SamplePlan(schema_name, object_name, normalized_type or "UNKNOWN", requested_rows, "NOT_APPLICABLE", "", False, "SKIPPED_UNSUPPORTED_OBJECT_TYPE")

    order_sql = " ORDER BY " + ", ".join(quote_identifier(column) for column in order_columns) if order_columns else ""
    sql = (
        f"SELECT TOP ({requested_rows}) * FROM "
        f"{quote_identifier(schema_name)}.{quote_identifier(object_name)}{order_sql}"
    )
    return SamplePlan(schema_name, object_name, normalized_type, requested_rows, strategy, sql)


def sanitize_sample_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    column_names: Sequence[str],
    classify: Callable[[str, Sequence[object]], SensitivityResult],
    salt: str,
) -> SanitizedSample:
    """Classify complete sampled columns and mask sensitive values before return."""
    classifications = {
        column: classify(column, tuple(row.get(column) for row in rows))
        for column in column_names
    }
    safe_rows = tuple({
        column: mask_value(row.get(column), classifications[column].category, salt, True)
        for column in column_names
    } for row in rows)
    masked_count = sum(result.category in SENSITIVE_CATEGORIES for result in classifications.values())
    return SanitizedSample(safe_rows, classifications, masked_count)


def sample_failure_status(error: object) -> str:
    text = str(error).casefold()
    if any(marker in text for marker in ("timeout", "timed out", "hyt00", "hyt01")):
        return "FAILED_TIMEOUT"
    if any(marker in text for marker in (
        "permission was denied", "select permission denied", "not authorized",
        "could not use view", "binding errors", "definition is encrypted",
    )):
        return "INACCESSIBLE"
    return "FAILED_QUERY"


__all__ = (
    "SamplePlan", "SanitizedSample", "build_sample_plan", "quote_identifier",
    "sample_failure_status", "sanitize_sample_rows",
)
