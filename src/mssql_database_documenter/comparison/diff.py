"""Stable record, timeline and numeric-delta comparison semantics."""

from __future__ import annotations

import difflib
import json
from typing import Any, Iterable

from .normalizers import number, stable_key, stable_text


def _pair_status(left: dict[str, Any] | None, right: dict[str, Any] | None, fields: tuple[str, ...], left_available: bool, right_available: bool) -> str:
    if not left_available and not right_available:
        return "NOT_AVAILABLE"
    if not left_available or not right_available:
        return "NOT_COMPARABLE"
    if left is None and right is None:
        return "NOT_AVAILABLE"
    if left is None:
        return "ADDED"
    if right is None:
        return "REMOVED"
    return "UNCHANGED" if all(stable_text(left.get(field)) == stable_text(right.get(field)) for field in fields) else "CHANGED"


def _timeline_events(records: list[dict[str, Any] | None], ab: str, bc: str, ac: str) -> list[str]:
    events: list[str] = []
    if ab == "ADDED": events.append("ADDED_IN_B")
    if bc == "ADDED": events.append("ADDED_IN_C")
    if ab == "REMOVED": events.append("REMOVED_IN_B")
    if bc == "REMOVED": events.append("REMOVED_IN_C")
    if ab == "CHANGED": events.append("CHANGED_A_TO_B")
    if bc == "CHANGED": events.append("CHANGED_B_TO_C")
    if ab == "CHANGED" and bc == "CHANGED" and ac == "UNCHANGED": events.append("REVERTED_TO_A")
    elif ab == "CHANGED" and bc == "CHANGED": events.append("CHANGED_BOTH")
    return events


def _timeline_pattern(events: list[str], ab: str, bc: str, ac: str) -> str:
    if "NOT_COMPARABLE" in {ab, bc, ac}: return "NOT_COMPARABLE"
    if {ab, bc, ac} == {"NOT_AVAILABLE"}: return "NOT_AVAILABLE"
    for priority in ("REVERTED_TO_A", "CHANGED_BOTH", "ADDED_IN_B", "ADDED_IN_C", "REMOVED_IN_B", "REMOVED_IN_C", "CHANGED_A_TO_B", "CHANGED_B_TO_C"):
        if priority in events: return priority
    if ab == bc == ac == "UNCHANGED": return "UNCHANGED"
    return "NOT_COMPARABLE"


def compare_rows(
    run_rows: dict[str, Iterable[dict[str, Any]]],
    key_fields: tuple[str, ...],
    compare_fields: tuple[str, ...],
    numeric_fields: tuple[str, ...] = (),
    definition_field: str | None = None,
    availability: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    labels = list(run_rows)
    if len(labels) not in {2, 3}:
        raise ValueError("Comparison requires exactly two or three runs")
    indexed = {
        label: {tuple(stable_key(row.get(field)) for field in key_fields): dict(row) for row in rows}
        for label, rows in run_rows.items()
    }
    available = availability or {label: True for label in labels}
    keys = sorted({key for rows in indexed.values() for key in rows})
    results: list[dict[str, Any]] = []
    for key in keys:
        records = {label: indexed[label].get(key) for label in labels}
        pairs = {"A_TO_B": _pair_status(records[labels[0]], records[labels[1]], compare_fields, available.get(labels[0], False), available.get(labels[1], False))}
        if len(labels) == 3:
            pairs["B_TO_C"] = _pair_status(records[labels[1]], records[labels[2]], compare_fields, available.get(labels[1], False), available.get(labels[2], False))
            pairs["A_TO_C"] = _pair_status(records[labels[0]], records[labels[2]], compare_fields, available.get(labels[0], False), available.get(labels[2], False))
            record_list = [records[label] for label in labels]
            events = _timeline_events(record_list, pairs["A_TO_B"], pairs["B_TO_C"], pairs["A_TO_C"])
            overall = _timeline_pattern(events, pairs["A_TO_B"], pairs["B_TO_C"], pairs["A_TO_C"])
        else:
            overall = pairs["A_TO_B"]
        row: dict[str, Any] = {"identity": dict(zip(key_fields, key, strict=True)), "status": overall, "intervals": pairs, "runs": {}}
        if len(labels) == 3:
            row["timeline_events"] = events
            if overall == "CHANGED_BOTH": row["legacy_status_alias"] = "CHANGED_BOTH_INTERVALS"
        for label in labels:
            record = records[label]
            row["runs"][label] = {field: stable_text(record.get(field)) for field in compare_fields} if record else None
        deltas: dict[str, Any] = {}
        for field in numeric_fields:
            values = [number((records[label] or {}).get(field)) for label in labels]
            field_delta: dict[str, Any] = {label: values[index] for index, label in enumerate(labels)}
            for left_index, right_index, name in ((0, 1, "B_MINUS_A"), (1, 2, "C_MINUS_B"), (0, 2, "C_MINUS_A")):
                if right_index >= len(values): continue
                left, right = values[left_index], values[right_index]
                field_delta[name] = None if left is None or right is None else right - left
                field_delta[name + "_PERCENT"] = None if left in (None, 0) or right is None else ((right - left) * 100.0 / left)
            deltas[field] = field_delta
        if deltas: row["numeric_deltas"] = deltas
        if definition_field:
            row["definitions"] = {
                label: stable_text((records[label] or {}).get(definition_field)) if records[label] else None
                for label in labels
            }
            diffs = {}
            for left_index, right_index, name in ((0, 1, "A_TO_B"), (1, 2, "B_TO_C"), (0, 2, "A_TO_C")):
                if right_index >= len(labels): continue
                left = stable_text((records[labels[left_index]] or {}).get(definition_field)).splitlines()
                right = stable_text((records[labels[right_index]] or {}).get(definition_field)).splitlines()
                if left != right:
                    diffs[name] = "\n".join(difflib.unified_diff(left, right, fromfile=labels[left_index], tofile=labels[right_index], lineterm=""))
            if diffs: row["definition_diffs"] = diffs
        results.append(row)
    return results
