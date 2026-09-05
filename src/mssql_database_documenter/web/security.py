"""Session, CSRF, same-origin and response-header controls."""

from __future__ import annotations

import secrets
from urllib.parse import urlparse

from flask import abort, current_app, request, session

from ..config import LOOPBACK_HOSTS


ALLOWED_ACTIONS = frozenset({"dry-run", "test-connection", "metadata", "metadata+logic", "safe-profile", "full-readonly", "reports"})


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return str(token)


def _same_origin() -> bool:
    if request.headers.get("Sec-Fetch-Site", "").casefold() in {"cross-site", "same-site"}:
        return False
    origin = request.headers.get("Origin") or request.headers.get("Referer")
    if not origin:
        return bool(current_app.testing)
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.netloc.casefold() == request.host.casefold()


def protect_request() -> None:
    request_hostname = (urlparse(f"//{request.host}").hostname or "").casefold()
    if request_hostname not in LOOPBACK_HOSTS:
        abort(400, description="Request host is not loopback")
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    if not _same_origin():
        abort(403, description="Action rejected: request is not same-origin")
    supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not supplied and request.is_json:
        supplied = (request.get_json(silent=True) or {}).get("csrf_token")
    if not supplied or not secrets.compare_digest(str(supplied), csrf_token()):
        abort(403, description="Action rejected: invalid CSRF token")


def add_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response
