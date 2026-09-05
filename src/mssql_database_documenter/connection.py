"""ODBC connection creation; no connection is opened unless explicitly requested."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from .config import Settings


def _odbc_escape(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def build_connection_string(settings: Settings, database: str) -> str:
    settings.validate_for_connection()
    parts = [
        f"DRIVER={_odbc_escape(settings.driver)}",
        f"SERVER={_odbc_escape(settings.server)}",
        f"DATABASE={_odbc_escape(database)}",
        f"Encrypt={'yes' if settings.encrypt else 'no'}",
        f"TrustServerCertificate={'yes' if settings.trust_server_certificate else 'no'}",
        "ApplicationIntent=ReadOnly",
        "APP=MSSQL Database Documenter",
    ]
    if settings.trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend((f"UID={_odbc_escape(settings.username)}", f"PWD={_odbc_escape(settings.password)}"))
    return ";".join(parts) + ";"


@contextmanager
def connect(settings: Settings, database: str) -> Iterator[object]:
    """Open one explicitly configured database with autocommit disabled."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for live connection commands") from exc
    connection = pyodbc.connect(
        build_connection_string(settings, database),
        timeout=settings.query_timeout_seconds,
        autocommit=False,
    )
    connection.timeout = settings.query_timeout_seconds
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()
