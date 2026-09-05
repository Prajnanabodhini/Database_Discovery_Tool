"""Strictly predefined control and read-only browsing APIs."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from ..config import VALID_MODES
from ..connection import connect
from ..fullrun import run_all
from ..git_export import create_git_export
from ..programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from ..queries import METADATA_QUERIES, QUERIES, get_query
from ..safety import ReadOnlyCursor, validate_read_only_sql
from .job_manager import JobConflictError
from .security import ALLOWED_ACTIONS


api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _settings(): return current_app.extensions["documenter_settings"]
def _browser(): return current_app.extensions["documenter_browser"]
def _jobs(): return current_app.extensions["documenter_jobs"]


def _selected_settings(database: str, mode: str):
    settings = _settings()
    if database and database not in settings.databases: raise ValueError("Database is not in the configured allowlist")
    if mode not in VALID_MODES: raise ValueError("Invalid discovery mode")
    return replace(settings, databases=(database,) if database else settings.databases, discovery_mode=mode)


def _target(action: str, settings):
    def execute(job, update):
        if action == "dry-run":
            validated = []
            for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
                validate_read_only_sql(query.sql)
                validated.append(query.name)
            return {"connection_attempted": False, "validated_query_count": len(validated), "warning_count": 0}
        if action == "test-connection":
            settings.validate_for_connection(); results = []
            for db in settings.databases:
                with connect(settings, db) as connection:
                    cursor = ReadOnlyCursor(connection.cursor())
                    query = get_query("connection_identity"); cursor.execute(query.sql); row = cursor.fetchone()
                    results.append({"database": db, "connected": bool(row)})
            return {"databases": results, "warning_count": 0}
        roots = run_all(settings, progress_callback=update, cancel_requested=job.cancel_event.is_set)
        warning_count = 0
        for root in roots:
            summary_path = root / "00_Run_Metadata" / "run_summary.json"
            if summary_path.is_file():
                summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
                count = int(summary.get("warning_error_count") or 0)
                warning_count += count
                if count:
                    job.warnings.append(f"{summary.get('database', root.parent.name)} recorded {count} warning/error item(s)")
        return {"run_directories": [str(path) for path in roots], "warning_count": warning_count}
    return execute


@api_blueprint.get("/config")
def config():
    settings = _settings(); current = _jobs().current()
    return jsonify({"configuration": settings.sanitized(), "read_only_guard": "PASS", "localhost_only": settings.web_host in {"127.0.0.1", "localhost", "::1"}, "active_job": current.public() if current else None})


@api_blueprint.post("/jobs/<action>")
def start_named_job(action: str):
    if action not in ALLOWED_ACTIONS: return jsonify({"error": "Action is not predefined"}), 400
    payload = request.get_json(silent=True) or {}; database = str(payload.get("database") or "")
    action_modes = {"metadata": "metadata", "metadata+logic": "metadata+logic", "safe-profile": "safe-profile", "full-readonly": "full-readonly", "reports": str(payload.get("mode") or _settings().discovery_mode), "dry-run": "metadata", "test-connection": "metadata"}
    mode = action_modes[action]
    try:
        selected = _selected_settings(database, mode)
        job = _jobs().start(action, database or ", ".join(_settings().databases), mode, _target(action, selected))
    except (ValueError, JobConflictError) as exc: return jsonify({"error": str(exc)}), 409 if isinstance(exc, JobConflictError) else 400
    return jsonify(job.public()), 202


@api_blueprint.post("/jobs/start")
def start_job():
    payload = request.get_json(silent=True) or {}; action = str(payload.get("action") or "")
    return start_named_job(action)


@api_blueprint.get("/jobs/current")
def current_job():
    job = _jobs().current(); return jsonify(job.public() if job else {"status": "IDLE"})


@api_blueprint.get("/jobs/<job_id>")
def job_detail(job_id: str):
    job = _jobs().get(job_id); return (jsonify(job.public()), 200) if job else (jsonify({"error": "Unknown job"}), 404)


@api_blueprint.get("/jobs/<job_id>/events")
def job_events(job_id: str): return job_detail(job_id)


@api_blueprint.post("/jobs/cancel")
def cancel_current():
    job = _jobs().current()
    if not job: return jsonify({"error": "No active job"}), 404
    return jsonify(_jobs().cancel(job.id).public())


@api_blueprint.get("/runs")
def runs(): return jsonify({"runs": _browser().scan_runs()})


@api_blueprint.get("/files")
def files():
    return jsonify(_browser().list_directory(request.args.get("root", "output"), request.args.get("path", ""), search=request.args.get("search", ""), extension=request.args.get("extension", "")))


@api_blueprint.get("/file")
def file_metadata():
    path = _browser().resolve(request.args.get("root", "output"), request.args.get("path", "")); stat = path.stat()
    return jsonify({"name": path.name, "size": stat.st_size, "modified": stat.st_mtime, "is_file": path.is_file()})


@api_blueprint.post("/git-export")
def git_export():
    payload = request.get_json(silent=True) or {}; reference = str(payload.get("run_ref") or "")
    try:
        snapshot = _browser().load_ref(reference)
        if snapshot.origin != "output": raise ValueError("Only an output run can be exported")
        settings = _settings()
        def target(job, update):
            destination = create_git_export(snapshot.root, output_root=settings.output_root, git_export_root=settings.git_export_root, sensitive_values=(settings.server, settings.username, settings.password))
            return {"git_export": str(destination), "warning_count": 0}
        job = _jobs().start("git-export", snapshot.database, str(snapshot.summary.get("mode") or "UNKNOWN"), target)
        return jsonify(job.public()), 202
    except (ValueError, JobConflictError) as exc: return jsonify({"error": str(exc)}), 400
