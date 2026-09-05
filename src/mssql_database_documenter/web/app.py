"""Flask application factory and loopback-only server launcher."""

from __future__ import annotations

from pathlib import Path
import secrets
import threading
import webbrowser

from flask import Flask, render_template

from ..config import Settings
from .file_browser import FileBrowser, PathSecurityError
from .job_manager import JobManager
from .security import add_security_headers, csrf_token, protect_request


def create_app(*, settings: Settings | None = None, env_file: Path = Path(".env"), testing: bool = False) -> Flask:
    settings = settings or Settings.from_environment(dotenv_path=env_file)
    settings.validate_for_web()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.testing = testing
    app.secret_key = secrets.token_bytes(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict", SESSION_COOKIE_SECURE=False, MAX_CONTENT_LENGTH=1_000_000)
    app.extensions["documenter_settings"] = settings
    app.extensions["documenter_browser"] = FileBrowser(settings.output_root, settings.git_export_root)
    app.extensions["documenter_jobs"] = JobManager(sensitive_values=(settings.server, settings.username, settings.password))
    app.extensions["documenter_comparisons"] = {}

    from .api import api_blueprint
    from .compare_api import compare_blueprint
    from .routes import pages_blueprint
    app.register_blueprint(pages_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(compare_blueprint)
    app.before_request(protect_request)
    app.after_request(add_security_headers)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.errorhandler(PathSecurityError)
    def path_error(exc): return render_template("error.html", title="Blocked path", message=str(exc)), 403

    @app.errorhandler(404)
    def not_found(exc): return render_template("error.html", title="Not found", message="The requested local resource does not exist."), 404

    @app.errorhandler(400)
    def bad_request(exc): return render_template("error.html", title="Request rejected", message="The local application rejected an invalid request."), 400

    @app.errorhandler(403)
    def forbidden(exc): return render_template("error.html", title="Action blocked", message="The local security policy blocked this request."), 403

    @app.errorhandler(500)
    def server_error(exc): return render_template("error.html", title="Local application error", message="The request failed. Review the controlled job log for sanitized details."), 500
    return app


def run_web(env_file: Path = Path(".env"), *, auto_open: bool = True) -> int:
    settings = Settings.from_environment(dotenv_path=env_file); settings.validate_for_web()
    app = create_app(settings=settings, env_file=env_file)
    url = f"http://{settings.web_host}:{settings.web_port}/"
    if auto_open and settings.web_auto_open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    app.run(host=settings.web_host, port=settings.web_port, debug=False, use_reloader=False)
    return 0
