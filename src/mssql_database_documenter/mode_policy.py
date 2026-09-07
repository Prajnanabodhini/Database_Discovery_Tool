"""Single, immutable execution contract for each discovery mode."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Settings


SAFE_SAMPLE_HARD_CEILING = 500
FULL_SAMPLE_HARD_CEILING = 2_000
SAFE_PROFILE_HARD_CEILING = 1_000_000
FULL_PROFILE_HARD_CEILING = 10_000_000
FULL_EXACT_COUNT_HARD_CEILING = 1_000_000
SAFE_RELATIONSHIP_HARD_CEILING = 1_000_000
FULL_RELATIONSHIP_HARD_CEILING = 10_000_000
SAFE_LOW_CARDINALITY_HARD_CEILING = 100
FULL_LOW_CARDINALITY_HARD_CEILING = 1_000


class ModePolicyError(ValueError):
    """Raised when configured mode limits exceed non-overridable safety ceilings."""


@dataclass(frozen=True, slots=True)
class ResolvedModePolicy:
    mode: str
    structural_catalog: bool
    programmable_logic: bool
    pipeline_metadata: bool
    data_profiles: bool
    samples: bool
    sample_tables: bool
    sample_views: bool
    sample_large_tables: bool
    sample_row_limit: int
    profile_row_threshold: int
    exact_counts: bool
    exact_count_ceiling: int
    relationship_validation: bool
    relationship_validation_threshold: int
    low_cardinality_limit: int
    extended_full_validation: bool

    @property
    def permits_data_scans(self) -> bool:
        return self.data_profiles or self.samples or self.exact_counts or self.relationship_validation

    def as_dict(self) -> dict[str, object]:
        return {**asdict(self), "permits_data_scans": self.permits_data_scans}


def _within_hard_ceiling(name: str, value: int, ceiling: int) -> int:
    if value < 1:
        raise ModePolicyError(f"{name} must be positive")
    if value > ceiling:
        raise ModePolicyError(f"{name} exceeds the hard ceiling of {ceiling}")
    return value


def resolve_mode_policy(settings: "Settings", mode: str | None = None) -> ResolvedModePolicy:
    selected = (mode or settings.discovery_mode).strip().casefold()
    if selected not in {"metadata", "metadata+logic", "safe-profile", "full-readonly"}:
        raise ModePolicyError(f"Unknown discovery mode: {selected}")

    if selected in {"metadata", "metadata+logic"}:
        logic = selected == "metadata+logic"
        return ResolvedModePolicy(
            mode=selected, structural_catalog=True, programmable_logic=logic,
            pipeline_metadata=logic, data_profiles=False, samples=False,
            sample_tables=False, sample_views=False, sample_large_tables=False,
            sample_row_limit=0, profile_row_threshold=0, exact_counts=False,
            exact_count_ceiling=0, relationship_validation=False,
            relationship_validation_threshold=0, low_cardinality_limit=0,
            extended_full_validation=False,
        )

    if selected == "safe-profile":
        sample_limit = _within_hard_ceiling("SAMPLE_ROW_LIMIT", settings.sample_row_limit, SAFE_SAMPLE_HARD_CEILING)
        profile_limit = _within_hard_ceiling("PROFILE_LARGE_TABLE_THRESHOLD", settings.profile_large_table_threshold, SAFE_PROFILE_HARD_CEILING)
        low_limit = 0
        if settings.profile_distinct_values:
            low_limit = _within_hard_ceiling("PROFILE_MAX_DISTINCT_VALUES", settings.profile_max_distinct_values, SAFE_LOW_CARDINALITY_HARD_CEILING)
        return ResolvedModePolicy(
            mode=selected, structural_catalog=True, programmable_logic=True,
            pipeline_metadata=True, data_profiles=True,
            samples=settings.sample_tables or settings.sample_views,
            sample_tables=settings.sample_tables, sample_views=settings.sample_views,
            sample_large_tables=settings.sample_large_tables, sample_row_limit=sample_limit,
            profile_row_threshold=profile_limit, exact_counts=False,
            exact_count_ceiling=0, relationship_validation=True,
            relationship_validation_threshold=min(profile_limit, SAFE_RELATIONSHIP_HARD_CEILING),
            low_cardinality_limit=low_limit, extended_full_validation=False,
        )

    safe_policy = resolve_mode_policy(settings, "safe-profile")
    sample_limit = _within_hard_ceiling(
        "FULL_READONLY_SAMPLE_ROW_LIMIT", settings.full_readonly_sample_row_limit,
        FULL_SAMPLE_HARD_CEILING,
    )
    profile_limit = _within_hard_ceiling(
        "FULL_READONLY_PROFILE_THRESHOLD", settings.full_readonly_profile_threshold,
        FULL_PROFILE_HARD_CEILING,
    )
    exact_limit = _within_hard_ceiling(
        "FULL_READONLY_EXACT_COUNT_THRESHOLD", settings.full_readonly_exact_count_threshold,
        FULL_EXACT_COUNT_HARD_CEILING,
    )
    relationship_limit = _within_hard_ceiling(
        "FULL_READONLY_RELATIONSHIP_THRESHOLD", settings.full_readonly_relationship_threshold,
        FULL_RELATIONSHIP_HARD_CEILING,
    )
    configured_low_limit = _within_hard_ceiling(
        "FULL_READONLY_LOW_CARDINALITY_LIMIT", settings.full_readonly_low_cardinality_limit,
        FULL_LOW_CARDINALITY_HARD_CEILING,
    )
    low_limit = configured_low_limit if settings.full_readonly_extended_validation else safe_policy.low_cardinality_limit
    comparisons = (
        ("FULL_READONLY_SAMPLE_ROW_LIMIT", sample_limit, safe_policy.sample_row_limit),
        ("FULL_READONLY_PROFILE_THRESHOLD", profile_limit, safe_policy.profile_row_threshold),
        ("FULL_READONLY_RELATIONSHIP_THRESHOLD", relationship_limit, safe_policy.relationship_validation_threshold),
        ("FULL_READONLY_LOW_CARDINALITY_LIMIT", low_limit, safe_policy.low_cardinality_limit),
    )
    for name, full_value, safe_value in comparisons:
        if full_value < safe_value:
            raise ModePolicyError(f"{name} cannot be lower than the resolved safe-profile value {safe_value}")
    if not settings.profile_exact_row_counts and not any(full_value > safe_value for _, full_value, safe_value in comparisons):
        raise ModePolicyError("full-readonly must resolve at least one limit deeper than safe-profile")
    return ResolvedModePolicy(
        mode=selected, structural_catalog=True, programmable_logic=True,
        pipeline_metadata=True, data_profiles=True,
        samples=settings.sample_tables or settings.sample_views,
        sample_tables=settings.sample_tables, sample_views=settings.sample_views,
        sample_large_tables=settings.sample_large_tables, sample_row_limit=sample_limit,
        profile_row_threshold=profile_limit,
        exact_counts=settings.profile_exact_row_counts,
        exact_count_ceiling=exact_limit if settings.profile_exact_row_counts else 0,
        relationship_validation=True,
        relationship_validation_threshold=relationship_limit,
        low_cardinality_limit=low_limit,
        extended_full_validation=settings.full_readonly_extended_validation,
    )


__all__ = (
    "FULL_EXACT_COUNT_HARD_CEILING", "FULL_LOW_CARDINALITY_HARD_CEILING",
    "FULL_PROFILE_HARD_CEILING", "FULL_RELATIONSHIP_HARD_CEILING",
    "FULL_SAMPLE_HARD_CEILING", "ModePolicyError", "ResolvedModePolicy",
    "SAFE_LOW_CARDINALITY_HARD_CEILING", "SAFE_PROFILE_HARD_CEILING",
    "SAFE_RELATIONSHIP_HARD_CEILING", "SAFE_SAMPLE_HARD_CEILING",
    "resolve_mode_policy",
)
