"""Human-facing pages; all state-changing work remains in controlled APIs."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request, send_file

from .renderers import render_file


pages_blueprint = Blueprint("pages", __name__)


def _settings(): return current_app.extensions["documenter_settings"]
def _browser(): return current_app.extensions["documenter_browser"]
def _jobs(): return current_app.extensions["documenter_jobs"]


@pages_blueprint.get("/")
def dashboard():
    settings = _settings(); current = _jobs().current()
    output_runs = [run for run in _browser().scan_runs() if run.get("root") == "output"][:8]
    return render_template("dashboard.html", title="Discovery dashboard", configuration=settings.sanitized(), current_job=current.public() if current else None, runs=output_runs)


@pages_blueprint.get("/help")
def help_page():
    return render_template("help.html", title="Help and operator guide")


@pages_blueprint.get("/browser")
def browser():
    root = request.args.get("root", "output"); relative = request.args.get("path", "")
    listing = _browser().list_directory(root, relative, search=request.args.get("search", ""), extension=request.args.get("extension", ""))
    return render_template("browser.html", title=f"{listing['label']} browser", listing=listing)


@pages_blueprint.get("/file")
def file_view():
    root = request.args.get("root", "output"); relative = request.args.get("path", "")
    path = _browser().resolve(root, relative)
    if not path.is_file(): return render_template("error.html", title="Not a file", message="Select a file to view."), 400
    rendered = render_file(path, page=request.args.get("page", 1, type=int), per_page=request.args.get("per_page", 50, type=int), search=request.args.get("search", ""), sort=request.args.get("sort", ""), descending=request.args.get("direction") == "desc")
    return render_template("file_view.html", title=path.name, root=root, relative=relative, rendered=rendered)


@pages_blueprint.get("/raw")
def raw_file():
    root = request.args.get("root", "output"); relative = request.args.get("path", ""); path = _browser().resolve(root, relative)
    return send_file(path, mimetype="text/plain; charset=utf-8", as_attachment=False, download_name=path.name)


@pages_blueprint.get("/download")
def download_file():
    root = request.args.get("root", "output"); relative = request.args.get("path", ""); path = _browser().resolve(root, relative)
    return send_file(path, as_attachment=True, download_name=path.name)


@pages_blueprint.get("/compare")
def compare_page(): return render_template("compare.html", title="Compare runs", runs=_browser().scan_runs(), enabled=_settings().enable_three_run_comparison)


@pages_blueprint.get("/run")
def run_detail():
    reference = request.args.get("ref", "")
    snapshot = _browser().load_ref(reference)
    checklist = snapshot.root / "99_Git_Handoff" / "SAFE_TO_COMMIT_CHECKLIST.md"
    checklist_status = "PRESENT" if checklist.is_file() else "NOT AVAILABLE"
    return render_template("run_detail.html", title=f"Run {snapshot.run_id}", run={**snapshot.summary, "database": snapshot.database, "run_id": snapshot.run_id, "origin": snapshot.origin, "path": reference, "browser_path": reference.partition(":")[2], "safe_to_commit_checklist": checklist_status})
