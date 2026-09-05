"""Production-safety helpers shared by profiling and sampling stages."""

from __future__ import annotations

from typing import Any


def known_row_estimate(table_sizes: dict[str, dict[str, Any]], key: str) -> int | None:
    """Return a trustworthy non-negative catalog estimate, or fail closed."""
    row = table_sizes.get(key)
    if not row:
        return None
    raw_value = row.get("row_count")
    if raw_value is None or raw_value == "":
        return None
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def within_safety_threshold(
    table_sizes: dict[str, dict[str, Any]], key: str, threshold: int,
) -> bool:
    estimate = known_row_estimate(table_sizes, key)
    return estimate is not None and estimate <= threshold


__all__ = ("known_row_estimate", "within_safety_threshold")
