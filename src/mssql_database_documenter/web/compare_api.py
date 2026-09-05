"""Explicit 2/3-run comparison API with in-memory pagination and optional export."""

from __future__ import annotations

import secrets

from flask import Blueprint, current_app, jsonify, request

from ..comparison import compare_run_paths, export_comparison


compare_blueprint = Blueprint("compare_api", __name__, url_prefix="/api/compare")


def _cache(): return current_app.extensions["documenter_comparisons"]
def _browser(): return current_app.extensions["documenter_browser"]
def _settings(): return current_app.extensions["documenter_settings"]


@compare_blueprint.post("")
def compare():
    payload = request.get_json(silent=True) or {}; references = payload.get("runs") or []
    if not isinstance(references, list) or len(references) not in {2, 3}: return jsonify({"error": "Select exactly two or three runs"}), 400
    if len(references) == 3 and not _settings().enable_three_run_comparison: return jsonify({"error": "Three-run comparison is disabled"}), 400
    if len(set(references)) != len(references): return jsonify({"error": "Each selected run must be different"}), 400
    try: result = compare_run_paths([_browser().load_ref(str(reference)) for reference in references])
    except ValueError as exc: return jsonify({"error": str(exc)}), 400
    comparison_id = secrets.token_urlsafe(12); _cache()[comparison_id] = result
    while len(_cache()) > 10: _cache().pop(next(iter(_cache())))
    exports = None
    if payload.get("export"):
        exports = {key: str(path) for key, path in export_comparison(result, _settings().output_root).items()}
    return jsonify({"id": comparison_id, "runs": result["runs"], "warnings": result["warnings"], "semantic_note": result["semantic_note"], "summary": result["summary"], "categories": {name: value["count"] for name, value in result["categories"].items()}, "category_metadata": {name: {"path": value["path"], "status": value["status"], "availability": value["availability"]} for name, value in result["categories"].items()}, "exports": exports})


@compare_blueprint.get("/<comparison_id>")
def comparison_rows(comparison_id: str):
    result = _cache().get(comparison_id)
    if not result: return jsonify({"error": "Comparison not found or expired"}), 404
    category = request.args.get("category", "tables")
    if category not in result["categories"]: return jsonify({"error": "Unknown comparison category"}), 400
    rows = result["categories"][category]["rows"]; status = request.args.get("status", ""); search = request.args.get("search", "").casefold()
    if status == "CHANGED_ONLY": rows = [row for row in rows if "CHANGED" in row["status"] or row["status"] == "REVERTED_TO_A"]
    elif status == "ADDED": rows = [row for row in rows if row["status"] == "ADDED" or row["status"].startswith("ADDED_IN_")]
    elif status == "REMOVED": rows = [row for row in rows if row["status"] == "REMOVED" or row["status"].startswith("REMOVED_IN_")]
    elif status: rows = [row for row in rows if row["status"] == status]
    if search: rows = [row for row in rows if search in str(row["identity"]).casefold()]
    schema = request.args.get("schema", "").casefold()
    if schema: rows = [row for row in rows if any("schema" in key.casefold() and schema in str(value).casefold() for key, value in row["identity"].items())]
    severity = request.args.get("severity", "").casefold()
    if severity: rows = [row for row in rows if severity in str(row.get("runs", {})).casefold() or severity in str(row["identity"]).casefold()]
    database = request.args.get("database", "").casefold()
    if database: rows = [row for row in rows if any(database == str(value).casefold() for value in row.get("databases", []))]
    if request.args.get("issues", "").casefold() in {"1", "true", "yes"}:
        rows = [row for row in rows if category in {"errors", "risks"} or row["status"] in {"NOT_AVAILABLE", "NOT_COMPARABLE"} or any(value in str(row).casefold() for value in ("warning", "error", "high", "medium", "critical"))]
    page = max(1, request.args.get("page", 1, type=int)); per_page = min(100, max(1, request.args.get("per_page", 25, type=int))); start = (page - 1) * per_page
    return jsonify({"category": category, "page": page, "per_page": per_page, "total": len(rows), "rows": rows[start:start + per_page]})
