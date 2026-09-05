"""Lineage classification vocabulary for static dependency analysis."""

LINEAGE_TYPES = frozenset({"DIRECT", "DERIVED", "AGGREGATED", "CONDITIONAL", "UNKNOWN"})

__all__ = ("LINEAGE_TYPES",)
