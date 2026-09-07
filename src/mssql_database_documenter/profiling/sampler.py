"""Bounded table/view sampling plans and pre-persistence masking."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable, Iterable, Mapping, Sequence

from .sensitivity import SENSITIVE_CATEGORIES, SensitivityResult, mask_value


TABLE_TYPES = frozenset({"TABLE", "USER_TABLE"})
VIEW_TYPES = frozenset({"VIEW"})
VIEW_SAMPLE_ALLOWED_STATUS = "ELIGIBLE_LOCAL_ONLY_VIEW"
VIEW_SAMPLE_DENIED_STATUS = "SKIPPED_EXTERNAL_OR_OPAQUE_VIEW_DEPENDENCY"
EXTERNAL_VIEW_PRIMITIVES = ("OPENQUERY", "OPENROWSET", "OPENDATASOURCE")


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
class ViewSampleEligibility:
    allowed: bool
    status: str
    reasons: tuple[str, ...]
    evidence_sources: tuple[str, ...]


def _source_matches(
    row: Mapping[str, object], schema_name: str, object_name: str,
) -> bool:
    return (
        str(row.get("source_schema") or "").casefold() == schema_name.casefold()
        and str(row.get("source_object") or "").casefold() == object_name.casefold()
    )


def _external_synonym_keys(
    synonyms: Iterable[Mapping[str, object]], current_database: str,
) -> set[tuple[str, str]]:
    external: set[tuple[str, str]] = set()
    database_key = current_database.strip("[]").casefold()
    for synonym in synonyms:
        base = str(synonym.get("base_object_name") or "")
        parts = [part.strip().strip("[]") for part in base.split(".") if part.strip()]
        is_external = len(parts) >= 4 or (
            len(parts) == 3 and parts[0].casefold() != database_key
        )
        if is_external:
            external.add((
                str(synonym.get("schema_name") or "").casefold(),
                str(synonym.get("object_name") or "").casefold(),
            ))
    return external


def evaluate_view_sample_eligibility(
    *,
    current_database: str,
    schema_name: str,
    object_name: str,
    view: Mapping[str, object] | None,
    dependencies: Iterable[Mapping[str, object]] = (),
    static_references: Iterable[Mapping[str, object]] = (),
    synonyms: Iterable[Mapping[str, object]] = (),
    dependency_discovery_complete: bool = True,
) -> ViewSampleEligibility:
    """Decide from discovered evidence whether sampling can stay database-local."""
    reasons: list[str] = []
    evidence = ["VIEW_CATALOGUE"]
    definition = str((view or {}).get("definition_sanitized") or "")
    definition_available = (
        _truthy(view.get("definition_available"))
        if view is not None and "definition_available" in view
        else bool(definition)
    )
    if view is None:
        reasons.append("VIEW_METADATA_UNAVAILABLE")
    elif not definition_available:
        reasons.append("VIEW_DEFINITION_UNAVAILABLE_OR_ENCRYPTED")
    else:
        evidence.append("SANITIZED_STATIC_DEFINITION")
    if view is not None and any(_truthy(view.get(field)) for field in (
        "dynamic_sql_present", "dynamic_sql_opaque", "definition_opaque",
        "dependency_resolution_opaque", "is_encrypted",
    )):
        reasons.append("VIEW_DEFINITION_DYNAMIC_OR_OPAQUE")
    for primitive in EXTERNAL_VIEW_PRIMITIVES:
        if re.search(rf"\b{primitive}\s*\(", definition, re.IGNORECASE):
            reasons.append(f"EXTERNAL_QUERY_PRIMITIVE_{primitive}")
    if not dependency_discovery_complete:
        reasons.append("DEPENDENCY_DISCOVERY_INCOMPLETE")
    else:
        evidence.append("SYS_SQL_EXPRESSION_DEPENDENCIES")

    external_synonyms = _external_synonym_keys(synonyms, current_database)
    if synonyms:
        evidence.append("SYNONYM_CATALOGUE")
    database_key = current_database.strip("[]").casefold()
    reference_groups = (
        (tuple(dependencies), True, "CATALOG_DEPENDENCY"),
        (tuple(static_references), False, "STATIC_REFERENCE"),
    )
    for references, catalog_evidence, evidence_name in reference_groups:
        matching = [
            row for row in references
            if _source_matches(row, schema_name, object_name)
        ]
        if matching:
            evidence.append(evidence_name)
        for row in matching:
            target_server = str(row.get("target_server") or "").strip()
            target_database = str(row.get("target_database") or "").strip().strip("[]")
            target_schema = str(row.get("target_schema") or "").casefold()
            target_object = str(row.get("target_object") or "").casefold()
            reference_kind = str(row.get("reference_kind") or "").upper()
            if target_server:
                reasons.append("LINKED_SERVER_DEPENDENCY")
            if target_database and target_database.casefold() != database_key:
                reasons.append("CROSS_DATABASE_DEPENDENCY")
            if reference_kind in {
                "FOUR_PART", "SYNONYM_EXTERNAL", *EXTERNAL_VIEW_PRIMITIVES,
            }:
                reasons.append("EXTERNAL_OR_OPAQUE_REFERENCE_KIND")
            if (
                (target_schema, target_object) in external_synonyms
                or ("", target_object) in external_synonyms
                or any(
                    synonym_object == target_object
                    and (not target_schema or synonym_schema == target_schema)
                    for synonym_schema, synonym_object in external_synonyms
                )
            ):
                reasons.append("EXTERNAL_SYNONYM_DEPENDENCY")
            if any(_truthy(row.get(field)) for field in (
                "is_ambiguous", "is_caller_dependent", "dynamic_sql_opaque",
                "dependency_resolution_opaque",
            )):
                reasons.append("AMBIGUOUS_OR_OPAQUE_DEPENDENCY")
            if (
                catalog_evidence
                and not row.get("referenced_id")
                and not (target_database and target_database.casefold() == database_key)
            ):
                reasons.append("UNRESOLVED_CATALOG_DEPENDENCY")

    unique_reasons = tuple(dict.fromkeys(reasons))
    unique_evidence = tuple(dict.fromkeys(evidence))
    return ViewSampleEligibility(
        allowed=not unique_reasons,
        status=VIEW_SAMPLE_ALLOWED_STATUS if not unique_reasons else VIEW_SAMPLE_DENIED_STATUS,
        reasons=unique_reasons,
        evidence_sources=unique_evidence,
    )


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
    eligibility_reason: str = ""
    eligibility_evidence: str = ""


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
    view_eligibility: ViewSampleEligibility | None = None,
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
        eligibility = view_eligibility or ViewSampleEligibility(
            False,
            VIEW_SAMPLE_DENIED_STATUS,
            ("VIEW_ELIGIBILITY_EVIDENCE_NOT_PROVIDED",),
            (),
        )
        if not eligibility.allowed:
            return SamplePlan(
                schema_name, object_name, normalized_type, requested_rows,
                "NOT_APPLICABLE", "", False, eligibility.status,
                ";".join(eligibility.reasons),
                ";".join(eligibility.evidence_sources),
            )
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
    "EXTERNAL_VIEW_PRIMITIVES", "SamplePlan", "SanitizedSample",
    "VIEW_SAMPLE_ALLOWED_STATUS", "VIEW_SAMPLE_DENIED_STATUS",
    "ViewSampleEligibility", "build_sample_plan",
    "evaluate_view_sample_eligibility", "quote_identifier",
    "sample_failure_status", "sanitize_sample_rows",
)
