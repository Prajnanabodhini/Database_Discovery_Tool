"""Truthful support-state evidence for optional/versioned MSSQL catalogues."""

from __future__ import annotations

from collections.abc import Iterable

from ..queries import QuerySpec


FEATURE_SUPPORT_HEADERS = (
    "feature_family",
    "query_name",
    "output_artifact",
    "status",
    "row_count",
    "evidence",
    "detail",
)

FEATURE_SUPPORT_STATES = frozenset(
    {"PRESENT", "ABSENT", "INACCESSIBLE", "UNSUPPORTED", "DISABLED"}
)


def is_unsupported_metadata_error(error: BaseException | str) -> bool:
    message = str(error).casefold()
    return any(
        marker in message
        for marker in (
            "invalid object name",
            "invalid column name",
            "is not a recognized built-in function name",
            "feature is not supported",
            "not supported in this version",
            "not supported on this edition",
        )
    )


def support_record(
    query: QuerySpec,
    *,
    row_count: int,
    state: str | None = None,
) -> dict[str, object]:
    status = state or ("PRESENT" if row_count else "ABSENT")
    if status not in FEATURE_SUPPORT_STATES:
        raise ValueError(f"Unknown metadata feature state: {status}")
    evidence, detail = {
        "PRESENT": ("CATALOG_QUERY_RETURNED_ROWS", "Feature metadata was visible to the reader."),
        "ABSENT": ("CATALOG_QUERY_RETURNED_ZERO_ROWS", "The catalogue was accessible but returned no matching rows visible to this reader; metadata visibility may still limit scope."),
        "INACCESSIBLE": ("CATALOG_QUERY_ACCESS_ERROR", "The catalogue could not be read with the current identity; absence is not inferred."),
        "UNSUPPORTED": ("CATALOG_NOT_SUPPORTED", "The catalog view or column is unavailable on this SQL Server version or edition."),
        "DISABLED": ("EXPLICIT_CONFIGURATION", f"Optional family requires {query.optional_setting}=true."),
    }[status]
    return {
        "feature_family": query.feature_family,
        "query_name": query.name,
        "output_artifact": f"{query.output_folder}/{query.output_name}",
        "status": status,
        "row_count": row_count,
        "evidence": evidence,
        "detail": detail,
    }


def feature_support_markdown(rows: Iterable[dict[str, object]]) -> str:
    values = list(rows)
    lines = [
        "# MSSQL Feature Support Overview",
        "",
        "States are evidence boundaries: `ABSENT` is used only after a successful zero-row query; `INACCESSIBLE` and `UNSUPPORTED` never imply absence.",
        "",
        "| Feature family | Status | Rows | Output artifact | Evidence |",
        "|---|---|---:|---|---|",
    ]
    for row in values:
        lines.append(
            f"| {row['feature_family']} | {row['status']} | {row['row_count']} | "
            f"`{row['output_artifact']}` | {row['evidence']} |"
        )
    if not values:
        lines.append("| None evaluated | INACCESSIBLE | 0 |  | No feature-support evidence was produced |")
    lines.extend(
        (
            "",
            "Optional security metadata defaults to disabled. When enabled, principal names are represented only by SHA-256 fingerprints; raw principal names and permission grants are not exported.",
        )
    )
    return "\n".join(lines) + "\n"
