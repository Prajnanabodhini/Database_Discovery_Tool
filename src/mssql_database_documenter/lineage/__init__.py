"""Lineage classification vocabulary for static dependency analysis."""

LINEAGE_TYPES = frozenset({"DIRECT", "DERIVED", "AGGREGATED", "CONDITIONAL", "UNKNOWN"})

from .agent import (  # noqa: E402
    RAW_COMMAND_FIELD,
    SQL_AGENT_PIPELINE_HEADERS,
    SQL_AGENT_REFERENCE_HEADERS,
    analyze_agent_steps,
)

__all__ = (
    "LINEAGE_TYPES",
    "RAW_COMMAND_FIELD",
    "SQL_AGENT_PIPELINE_HEADERS",
    "SQL_AGENT_REFERENCE_HEADERS",
    "analyze_agent_steps",
)
