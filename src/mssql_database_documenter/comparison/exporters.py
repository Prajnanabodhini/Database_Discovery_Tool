"""Explicit comparison export; never invoked by application construction."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any

from ..path_safety import ensure_contained_directory


def _escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)


def _pre(value: object) -> str:
    return f"<pre>{_escaped(_json_text(value))}</pre>"


def _summary_html(title: str, summary: dict[str, Any]) -> str:
    primary = "".join(
        f"<li><strong>{_escaped(status)}</strong>: {int(count)}</li>"
        for status, count in summary.get("primary_status_counts", {}).items()
    ) or "<li>No comparison rows.</li>"
    intervals = "".join(
        f"<li><strong>{_escaped(status)}</strong>: {int(count)}</li>"
        for status, count in summary.get("interval_status_occurrences", {}).items()
    ) or "<li>No interval occurrences.</li>"
    events = "".join(
        f"<li><strong>{_escaped(status)}</strong>: {int(count)}</li>"
        for status, count in summary.get("timeline_event_occurrences", {}).items()
    ) or "<li>No three-run timeline events.</li>"
    return (
        f"<section><h2>{_escaped(title)}</h2>"
        f"<p><strong>Scope:</strong> {_escaped(summary.get('scope', 'UNKNOWN'))}. "
        f"<strong>Rows:</strong> {int(summary.get('row_count', 0))}.</p>"
        f"<p>{_escaped(summary.get('scope_note') or summary.get('counting_note') or '')}</p>"
        "<h3>Primary status counts</h3><ul>" + primary + "</ul>"
        "<h3>Interval status occurrences</h3><ul>" + intervals + "</ul>"
        "<h3>Timeline event occurrences</h3><ul>" + events + "</ul></section>"
    )


def _definition_html(row: dict[str, Any], labels: list[str]) -> str:
    definitions = row.get("definitions") or {}
    diffs = row.get("definition_diffs") or {}
    if not definitions and not diffs:
        return "<span>Not applicable</span>"
    parts = ["<details open><summary>Definition sources and interval diffs</summary>"]
    for label in labels:
        if label in definitions:
            source = "NOT AVAILABLE" if definitions[label] is None else definitions[label]
            parts.append(f"<h4>Run {_escaped(label)}</h4><pre>{_escaped(source)}</pre>")
    for interval in ("A_TO_B", "B_TO_C", "A_TO_C"):
        if interval in diffs:
            parts.append(f"<h4>{_escaped(interval.replace('_TO_', '→'))}</h4><pre>{_escaped(diffs[interval])}</pre>")
    parts.append("</details>")
    return "".join(parts)


def _static_html(result: dict[str, Any]) -> str:
    labels = list(result.get("runs", {}))
    run_rows = []
    for label, metadata in result.get("runs", {}).items():
        run_rows.append(
            "<tr>"
            f"<th scope='row'>Run {_escaped(label)}</th>"
            f"<td>{_escaped(metadata.get('database', 'UNKNOWN'))}</td>"
            f"<td>{_escaped(metadata.get('run_id') or metadata.get('label') or '')}</td>"
            f"<td>{_escaped(metadata.get('timestamp_utc', ''))}</td>"
            f"<td>{_escaped(metadata.get('mode', ''))}</td>"
            f"<td>{_escaped(metadata.get('status', ''))}</td>"
            "</tr>"
        )
    warnings = "".join(f"<li>{_escaped(item)}</li>" for item in result.get("warnings", [])) or "<li>No comparison warnings.</li>"
    sections = []
    interval_columns = ["A_TO_B"] + (["B_TO_C", "A_TO_C"] if "C" in labels else [])
    for category, payload in result.get("categories", {}).items():
        headers = ["Identity", "Primary status", "Timeline events"]
        headers.extend(f"Run {label}" for label in labels)
        headers.extend(name.replace("_TO_", "→") for name in interval_columns)
        headers.extend(("Numeric values/deltas", "Definition sources/diffs"))
        header_html = "".join(f"<th scope='col'>{_escaped(name)}</th>" for name in headers)
        body = []
        for row in payload.get("rows", []):
            cells = [
                _pre(row.get("identity", {})),
                f"<strong>{_escaped(row.get('status', 'UNKNOWN'))}</strong>",
                _pre(row.get("timeline_events", [])),
            ]
            cells.extend(_pre((row.get("runs") or {}).get(label)) for label in labels)
            cells.extend(
                f"<strong>{_escaped((row.get('intervals') or {}).get(interval, 'NOT APPLICABLE'))}</strong>"
                for interval in interval_columns
            )
            cells.append(_pre(row.get("numeric_deltas", {})))
            cells.append(_definition_html(row, labels))
            body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        if not body:
            body.append(f"<tr><td colspan='{len(headers)}'>No comparison rows in this category.</td></tr>")
        availability = ", ".join(
            f"{label}={'available' if available else 'unavailable'}"
            for label, available in payload.get("availability", {}).items()
        )
        sections.append(
            f"<section><h2>{_escaped(category)}</h2>"
            f"<p><strong>Source:</strong> {_escaped(payload.get('path', ''))}. "
            f"<strong>Evidence status:</strong> {_escaped(payload.get('status', 'UNKNOWN'))}. "
            f"<strong>Availability:</strong> {_escaped(availability)}.</p>"
            + _summary_html("Category summary", payload.get("summary", {}))
            + f"<div><table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"
        )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Run comparison export</title>"
        "<style>body{font:14px system-ui;margin:2rem;color:#172033}section{margin:2rem 0}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd5e0;padding:.55rem;vertical-align:top}pre{white-space:pre-wrap;margin:0;max-width:38rem}div{overflow:auto}</style>"
        "</head><body><main><header><h1>Run comparison export</h1>"
        f"<p>{_escaped(result.get('semantic_note', ''))}</p></header>"
        "<section><h2>Run metadata</h2><table><thead><tr><th>Run</th><th>Database</th><th>Run ID</th><th>Timestamp UTC</th><th>Mode</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(run_rows)}</tbody></table></section>"
        f"<section><h2>Warnings</h2><ul>{warnings}</ul></section>"
        + _summary_html("Global summary", result.get("summary", {}))
        + "".join(sections)
        + "</main></body></html>\n"
    )


def export_comparison(result: dict[str, Any], output_root: Path, *, fixed_names: bool = False) -> dict[str, Path]:
    if fixed_names:
        destination = ensure_contained_directory(output_root)
        stem = "DATABASE_COMPARISON"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        destination = ensure_contained_directory(
            output_root,
            ("comparisons", f"compare_{stamp}"),
        )
        stem = "comparison"
    json_path = destination / f"{stem}.json"
    csv_path = destination / f"{stem}.csv"
    html_path = destination / f"{stem}.html"
    json_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("category", "status", "identity", "timeline_events", "intervals", "runs", "numeric_deltas", "definitions", "definition_diffs"))
        writer.writeheader()
        for category, payload in result["categories"].items():
            for row in payload["rows"]:
                writer.writerow({"category": category, "status": row["status"], "identity": json.dumps(row["identity"], sort_keys=True), "timeline_events": json.dumps(row.get("timeline_events", []), sort_keys=True), "intervals": json.dumps(row["intervals"], sort_keys=True), "runs": json.dumps(row["runs"], sort_keys=True), "numeric_deltas": json.dumps(row.get("numeric_deltas", {}), sort_keys=True), "definitions": json.dumps(row.get("definitions", {}), sort_keys=True), "definition_diffs": json.dumps(row.get("definition_diffs", {}), sort_keys=True)})
    html_path.write_text(_static_html(result), encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "html": html_path}
