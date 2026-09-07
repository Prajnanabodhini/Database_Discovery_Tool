"""Production-safety helpers shared by profiling and sampling stages."""

from __future__ import annotations

from typing import Any

from .sensitivity import (
    SENSITIVE_CATEGORIES,
    SensitivityResult,
    SensitivityRule,
    classify_sensitivity,
    load_sensitivity_overrides,
    mask_value,
)
from .sampler import (
    EXTERNAL_VIEW_PRIMITIVES,
    SamplePlan,
    SanitizedSample,
    VIEW_SAMPLE_ALLOWED_STATUS,
    VIEW_SAMPLE_DENIED_STATUS,
    ViewSampleEligibility,
    build_sample_plan,
    evaluate_view_sample_eligibility,
    sample_failure_status,
    sanitize_sample_rows,
)


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


__all__ = (
    "EXTERNAL_VIEW_PRIMITIVES", "SENSITIVE_CATEGORIES", "SensitivityResult",
    "SensitivityRule", "VIEW_SAMPLE_ALLOWED_STATUS", "VIEW_SAMPLE_DENIED_STATUS",
    "ViewSampleEligibility", "classify_sensitivity",
    "SamplePlan", "SanitizedSample", "build_sample_plan",
    "evaluate_view_sample_eligibility", "known_row_estimate",
    "load_sensitivity_overrides", "mask_value", "sample_failure_status",
    "sanitize_sample_rows",
    "within_safety_threshold",
)
