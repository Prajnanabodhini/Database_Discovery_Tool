"""Explicit comparison export; never invoked by application construction."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def export_comparison(result: dict[str, Any], output_root: Path, *, fixed_names: bool = False) -> dict[str, Path]:
    if fixed_names:
        destination = output_root
        stem = "DATABASE_COMPARISON"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        destination = output_root / "comparisons" / f"compare_{stamp}"
        stem = "comparison"
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / f"{stem}.json"
    csv_path = destination / f"{stem}.csv"
    html_path = destination / f"{stem}.html"
    json_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("category", "status", "identity", "intervals", "runs", "numeric_deltas", "definitions", "definition_diffs"))
        writer.writeheader()
        for category, payload in result["categories"].items():
            for row in payload["rows"]:
                writer.writerow({"category": category, "status": row["status"], "identity": json.dumps(row["identity"], sort_keys=True), "intervals": json.dumps(row["intervals"], sort_keys=True), "runs": json.dumps(row["runs"], sort_keys=True), "numeric_deltas": json.dumps(row.get("numeric_deltas", {}), sort_keys=True), "definitions": json.dumps(row.get("definitions", {}), sort_keys=True), "definition_diffs": json.dumps(row.get("definition_diffs", {}), sort_keys=True)})
    safe_payload = json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html_path.write_text("<!doctype html><html><head><meta charset='utf-8'><title>Run comparison</title><style>body{font:14px system-ui;margin:2rem;background:#f4f7fb;color:#172033}pre{white-space:pre-wrap;background:white;padding:1rem;border-radius:12px}</style></head><body><h1>Run comparison export</h1><p>Canonical full JSON is embedded below without row loss.</p><pre id='data'></pre><script type='application/json' id='payload'>" + safe_payload + "</script><script>document.getElementById('data').textContent=JSON.stringify(JSON.parse(document.getElementById('payload').textContent),null,2)</script></body></html>\n", encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "html": html_path}
