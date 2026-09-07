"""Offline, source-preserving regeneration of presentation reports."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
from typing import Iterable
import uuid

from .comparison.loaders import RunSnapshot
from .inventory import safe_path_component
from .path_safety import (
    ensure_contained_directory,
    is_reparse_point,
    new_contained_path,
)
from .redaction import redact_text


_CATALOGUES = (
    ("Tables", "04_Tables/TABLE_CATALOGUE.csv"),
    ("Columns", "05_Columns/COLUMN_CATALOGUE.csv"),
    ("Views", "10_Views/VIEW_CATALOGUE.csv"),
    ("Procedures", "11_Programmable_Objects/STORED_PROCEDURES.csv"),
    ("Functions", "11_Programmable_Objects/FUNCTIONS.csv"),
    ("Triggers", "11_Programmable_Objects/TRIGGERS.csv"),
    ("Discovery errors", "00_Run_Metadata/DISCOVERY_ERRORS.csv"),
)


def _source_inventory(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(root).as_posix()
        if is_reparse_point(path):
            raise ValueError(f"Canonical source contains a symbolic link or reparse point: {relative}")
        if path.is_file():
            content = path.read_bytes()
            records.append({
                "path": relative,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            })
    return records


def _catalogue_counts(snapshot: RunSnapshot) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for label, relative in _CATALOGUES:
        path = snapshot.root / relative
        if not path.is_file():
            result.append({"label": label, "artifact": relative, "rows": "NOT AVAILABLE"})
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows: int | str = sum(1 for _ in csv.DictReader(handle))
        except (OSError, csv.Error, UnicodeError):
            rows = "UNREADABLE"
        result.append({"label": label, "artifact": relative, "rows": rows})
    return result


def _redacted(value: object, sensitive_values: tuple[str, ...]) -> str:
    return redact_text(value, sensitive_values=sensitive_values)


def _quoted_markdown(value: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in value.splitlines())


def _write_reports(
    staging: Path,
    snapshot: RunSnapshot,
    inventory: list[dict[str, object]],
    sensitive_values: tuple[str, ...],
) -> tuple[Path, Path]:
    database = _redacted(snapshot.database, sensitive_values)
    run_id = _redacted(snapshot.run_id, sensitive_values)
    mode = _redacted(snapshot.summary.get("mode") or "UNKNOWN", sensitive_values)
    status = _redacted(snapshot.summary.get("status") or "UNKNOWN", sensitive_values)
    canonical_summary = _redacted(
        snapshot.text("01_Executive_Summary/MSSQL_EXECUTIVE_SUMMARY.md")
        or "Canonical executive summary is not available in this run.",
        sensitive_values,
    )
    coverage = _redacted(
        snapshot.text("00_Run_Metadata/DISCOVERY_COVERAGE.md")
        or "Discovery coverage narrative is not available in this run.",
        sensitive_values,
    )
    warnings = [
        _redacted(item, sensitive_values)
        for item in (snapshot.manifest.get("warnings") or [])
    ]
    counts = _catalogue_counts(snapshot)

    markdown_lines = [
        "# Regenerated report",
        "",
        "> Presentation-only copy generated from an existing canonical run. No MSSQL connection was attempted and the canonical source was not modified.",
        "",
        "## Source run",
        "",
        f"- Database: `{database}`",
        f"- Run ID: `{run_id}`",
        f"- Mode: `{mode}`",
        f"- Status: `{status}`",
        f"- Canonical source files verified: `{len(inventory)}`",
        "",
        "## Catalogue coverage",
        "",
        "| Category | Canonical artifact | Rows |",
        "|---|---|---:|",
    ]
    markdown_lines.extend(
        f"| {_redacted(item['label'], sensitive_values)} | `{_redacted(item['artifact'], sensitive_values)}` | {item['rows']} |"
        for item in counts
    )
    markdown_lines.extend([
        "",
        "## Canonical executive summary",
        "",
        _quoted_markdown(canonical_summary),
        "",
        "## Canonical discovery coverage",
        "",
        _quoted_markdown(coverage),
        "",
        "## Canonical warnings",
        "",
    ])
    markdown_lines.extend(f"- {_redacted(item, sensitive_values)}" for item in warnings)
    if not warnings:
        markdown_lines.append("- No warnings were recorded in the source manifest.")
    markdown_lines.extend([
        "",
        "## Source artifact inventory",
        "",
        "| Canonical artifact | Bytes | SHA-256 |",
        "|---|---:|---|",
    ])
    markdown_lines.extend(
        f"| `{_redacted(item['path'], sensitive_values)}` | {item['bytes']} | `{item['sha256']}` |"
        for item in inventory
    )
    markdown_path = staging / "01_Executive_Summary" / "REGENERATED_REPORT.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    count_rows = "".join(
        "<tr><td>{}</td><td><code>{}</code></td><td>{}</td></tr>".format(
            escape(_redacted(item["label"], sensitive_values)),
            escape(_redacted(item["artifact"], sensitive_values)),
            escape(str(item["rows"])),
        )
        for item in counts
    )
    warning_items = "".join(f"<li>{escape(item)}</li>" for item in warnings) or "<li>No warnings were recorded in the source manifest.</li>"
    inventory_rows = "".join(
        "<tr><td><code>{}</code></td><td>{}</td><td><code>{}</code></td></tr>".format(
            escape(_redacted(item["path"], sensitive_values)), item["bytes"], item["sha256"]
        )
        for item in inventory
    )
    html_source = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Regenerated report - {escape(database)}</title></head>
<body><main>
<header><p>Offline presentation artifact</p><h1>Regenerated report</h1>
<p>This presentation-only copy was generated from an existing canonical run. No MSSQL connection was attempted and the canonical source was not modified.</p></header>
<section><h2>Source run</h2><dl>
<dt>Database</dt><dd>{escape(database)}</dd><dt>Run ID</dt><dd>{escape(run_id)}</dd>
<dt>Mode</dt><dd>{escape(mode)}</dd><dt>Status</dt><dd>{escape(status)}</dd>
<dt>Canonical source files verified</dt><dd>{len(inventory)}</dd></dl></section>
<section><h2>Catalogue coverage</h2><table><thead><tr><th>Category</th><th>Canonical artifact</th><th>Rows</th></tr></thead><tbody>{count_rows}</tbody></table></section>
<section><h2>Canonical executive summary</h2><pre>{escape(canonical_summary)}</pre></section>
<section><h2>Canonical discovery coverage</h2><pre>{escape(coverage)}</pre></section>
<section><h2>Canonical warnings</h2><ul>{warning_items}</ul></section>
<section><h2>Source artifact inventory</h2><table><thead><tr><th>Canonical artifact</th><th>Bytes</th><th>SHA-256</th></tr></thead><tbody>{inventory_rows}</tbody></table></section>
</main></body></html>
"""
    html_path = staging / "21_HTML_Report" / "REGENERATED_REPORT.html"
    html_path.parent.mkdir(parents=True)
    html_path.write_text(html_source, encoding="utf-8")
    return markdown_path, html_path


def regenerate_reports(
    snapshot: RunSnapshot,
    output_root: Path | str,
    *,
    sensitive_values: Iterable[str] = (),
) -> dict[str, Path]:
    """Regenerate presentation artifacts from one manifested output run, offline."""
    source = snapshot.root.resolve(strict=True)
    output = Path(output_root).resolve(strict=True)
    try:
        source_relative = source.relative_to(output)
    except ValueError as exc:
        raise ValueError("Canonical source run is outside the configured output root") from exc
    if source_relative.parts and source_relative.parts[0].casefold() == "report_regenerations":
        raise ValueError("A regenerated presentation cannot be used as canonical source")
    if not (source / "00_Run_Metadata" / "manifest.json").is_file() and not (source / "manifest.json").is_file():
        raise ValueError("Canonical source run has no manifest.json")

    secrets = tuple(str(item) for item in sensitive_values if item)
    before = _source_inventory(source)
    database_component = safe_path_component(_redacted(snapshot.database, secrets))
    run_component = safe_path_component(_redacted(snapshot.run_id, secrets))
    base_components = ("report_regenerations", database_component, run_component)
    ensure_contained_directory(output, base_components)

    regeneration_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f") + "_" + uuid.uuid4().hex[:8]
    destination = new_contained_path(
        output,
        (*base_components, f"regen_{regeneration_id}"),
    )
    staging_component = f".regen_{regeneration_id}.partial"
    staging = ensure_contained_directory(
        output,
        (*base_components, staging_component),
    )
    markdown_staging, html_staging = _write_reports(staging, snapshot, before, secrets)

    manifest_staging = staging / "00_Run_Metadata" / "REPORT_REGENERATION_MANIFEST.json"
    manifest_staging.parent.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "regeneration_id": regeneration_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "database": _redacted(snapshot.database, secrets),
        "source_run_id": _redacted(snapshot.run_id, secrets),
        "source_mode": _redacted(snapshot.summary.get("mode") or "UNKNOWN", secrets),
        "source_status": _redacted(snapshot.summary.get("status") or "UNKNOWN", secrets),
        "source_run_relative": _redacted(source_relative.as_posix(), secrets),
        "source_file_count": len(before),
        "source_artifacts": [
            {**item, "path": _redacted(item["path"], secrets)} for item in before
        ],
        "database_connection_attempted": False,
        "canonical_source_mutated": False,
        "outputs": [
            markdown_staging.relative_to(staging).as_posix(),
            html_staging.relative_to(staging).as_posix(),
        ],
        "source_warnings": [
            _redacted(item, secrets) for item in (snapshot.manifest.get("warnings") or [])
        ],
    }
    manifest_staging.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksums_staging = staging / "00_Run_Metadata" / "checksums.sha256"
    checksum_lines = []
    for path in sorted(staging.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_file() and path != checksums_staging:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            checksum_lines.append(f"{digest}  {path.relative_to(staging).as_posix()}")
    checksums_staging.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    after = _source_inventory(source)
    if after != before:
        raise RuntimeError("Canonical source changed during report regeneration")
    ensure_contained_directory(
        output,
        (*base_components, staging_component),
        create=False,
    )
    destination = new_contained_path(
        output,
        (*base_components, f"regen_{regeneration_id}"),
    )
    staging.rename(destination)
    ensure_contained_directory(
        output,
        (*base_components, destination.name),
        create=False,
    )
    return {
        "destination": destination,
        "html": destination / html_staging.relative_to(staging),
        "markdown": destination / markdown_staging.relative_to(staging),
        "manifest": destination / manifest_staging.relative_to(staging),
        "checksums": destination / checksums_staging.relative_to(staging),
    }
