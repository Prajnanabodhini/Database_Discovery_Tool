"""Command-line entry point for staged, read-only discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import ConfigurationError, Settings
from .programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from .queries import METADATA_QUERIES, QUERIES, get_query
from .redaction import redact_text
from .safety import ReadOnlyCursor, UnsafeSqlError, validate_read_only_sql


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mssql-documenter")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--database", help="Process only this explicitly named database")
    parser.add_argument("--mode", choices=("metadata", "metadata+logic", "safe-profile", "full-readonly"), help="Override DISCOVERY_MODE for this run")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("dry-run", help="Validate all registered SQL without connecting")
    subparsers.add_parser("test-connection", help="Connect and run read-only capability queries")
    subparsers.add_parser("inventory", help="Create a metadata-only catalogue for configured databases")
    subparsers.add_parser("all", help="Run every read-only discovery prompt sequentially")
    subparsers.add_parser("programmable-objects", help="Run prerequisites through static programmable-object discovery")
    subparsers.add_parser("profile", help="Run prerequisites through safe profiling and sensitivity reporting")
    subparsers.add_parser("relationships", help="Run prerequisites through relationship analysis")
    subparsers.add_parser("lineage", help="Run prerequisites through lineage and external-reference analysis")
    subparsers.add_parser("pipelines", help="Run prerequisites through pipeline analysis")
    subparsers.add_parser("report", help="Run the complete pipeline and final reporting")
    return parser


def _dry_run(settings: Settings) -> int:
    validated = []
    for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
        validate_read_only_sql(query.sql)
        validated.append({"name": query.name, "stage": query.stage, "status": "SAFE"})
    print(json.dumps({"status": "PASS", "connection_attempted": False, "queries": validated, "configuration": settings.sanitized()}, indent=2))
    return 0


def _test_connection(settings: Settings) -> int:
    from .connection import connect

    settings.validate_for_connection()
    results: list[dict[str, object]] = []
    for database in settings.databases:
        with connect(settings, database) as connection:
            cursor = ReadOnlyCursor(connection.cursor())
            for query_name in ("connection_identity", "server_capabilities", "database_capabilities"):
                query = get_query(query_name)
                cursor.execute(query.sql)
                columns = [description[0] for description in cursor.description]
                rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
                for row in rows:
                    if settings.sanitize_server_name and "server_name" in row:
                        row["server_name"] = "[SANITIZED]"
                    if "login_name" in row:
                        row["login_name"] = "[REDACTED]"
                results.append({"database": database, "query": query_name, "rows": rows})
    print(json.dumps({"status": "PASS", "configuration": settings.sanitized(), "results": results}, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings: Settings | None = None
    try:
        settings = Settings.from_environment(dotenv_path=args.env_file).with_database_override(args.database).with_mode_override(args.mode)
        if args.command == "dry-run":
            return _dry_run(settings)
        if args.command == "test-connection":
            return _test_connection(settings)
        if args.command == "inventory":
            from .inventory import run_inventory

            settings.validate_for_connection()
            results = [run_inventory(settings, database) for database in settings.databases]
            print(json.dumps({
                "status": "PASS" if all(result.error_count == 0 for result in results) else "PASS_WITH_WARNINGS",
                "stage": "metadata",
                "results": [
                    {
                        "database": result.database,
                        "run_directory": str(result.run_directory),
                        "query_count": result.query_count,
                        "error_count": result.error_count,
                        "row_counts": result.row_counts,
                    }
                    for result in results
                ],
            }, indent=2))
            return 0
        if args.command in {"all", "report"}:
            from .fullrun import run_all

            roots = run_all(settings)
            print(json.dumps({"status": "PASS", "stage": args.command, "run_directories": [str(path) for path in roots]}, indent=2))
            return 0
        stage_commands = {
            "programmable-objects": "05", "profile": "09", "relationships": "10",
            "pipelines": "11", "lineage": "12",
        }
        if args.command in stage_commands:
            from .fullrun import run_until

            if args.mode is None:
                required_modes = {
                    "programmable-objects": "metadata+logic", "profile": "safe-profile",
                    "relationships": "safe-profile", "lineage": "metadata+logic", "pipelines": "metadata+logic",
                }
                settings = settings.with_mode_override(required_modes[args.command])
            roots = run_until(settings, stage_commands[args.command])
            print(json.dumps({"status": "PASS", "stage": args.command, "run_directories": [str(path) for path in roots]}, indent=2))
            return 0
        raise ConfigurationError(f"Unsupported command: {args.command}")
    except Exception as exc:
        sensitive_values = ()
        if settings is not None:
            sensitive_values = (settings.password, settings.username, settings.server)
        print(f"ERROR: {redact_text(exc, sensitive_values=sensitive_values)}", file=sys.stderr)
        return 2
