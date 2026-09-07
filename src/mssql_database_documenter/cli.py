"""Command-line entry point for staged, read-only discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

from .config import ConfigurationError, Settings
from .mode_policy import resolve_mode_policy
from .programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from .queries import METADATA_QUERIES, QUERIES, SECURITY_METADATA_QUERIES, get_query
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
    subparsers.add_parser("all", help="Connect to MSSQL for a new live read-only discovery and generate its reports")
    subparsers.add_parser("discover-and-report", help="Explicit alias for a new live read-only discovery with normal reports")
    regenerate = subparsers.add_parser(
        "regenerate-reports",
        help="Regenerate presentation reports offline from one existing manifested output run",
    )
    regenerate.add_argument(
        "--run", required=True,
        help="Manifested output run path or output:<database/run_id> reference",
    )
    subparsers.add_parser("programmable-objects", help="Run prerequisites through static programmable-object discovery")
    subparsers.add_parser("profile", help="Run prerequisites through safe profiling and sensitivity reporting")
    subparsers.add_parser("relationships", help="Run prerequisites through relationship analysis")
    subparsers.add_parser("lineage", help="Run prerequisites through lineage and external-reference analysis")
    subparsers.add_parser("pipelines", help="Run prerequisites through pipeline analysis")
    return parser


def _load_output_run(reference: str, output_root: Path):
    """Resolve one contained manifested output run without touching MSSQL."""
    from .comparison import load_run

    root = output_root.resolve(strict=True)
    if reference.startswith("output:"):
        relative = reference.removeprefix("output:")
        pure = PurePosixPath(relative.replace(chr(92), "/"))
        if (
            not relative or pure.is_absolute() or PureWindowsPath(relative).is_absolute()
            or ".." in pure.parts
        ):
            raise ConfigurationError("Invalid or unsafe output run reference")
        candidate = (root / Path(*pure.parts)).resolve(strict=True)
    else:
        supplied = Path(reference)
        if supplied.is_absolute() or PureWindowsPath(reference).is_absolute():
            candidate = supplied.resolve(strict=True)
        else:
            direct = supplied.resolve(strict=False)
            candidate = (
                direct.resolve(strict=True)
                if direct.exists()
                else (root / supplied).resolve(strict=True)
            )
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ConfigurationError("Selected report source is outside OUTPUT_ROOT") from exc
    return load_run(candidate, label=reference, origin="output")


def _regenerate_reports_command(settings: Settings, reference: str) -> int:
    from .report_regeneration import regenerate_reports

    sensitive_values = (settings.server, settings.username, settings.password)
    snapshot = _load_output_run(reference, settings.output_root)
    result = regenerate_reports(
        snapshot,
        settings.output_root,
        sensitive_values=sensitive_values,
    )
    safe = {
        name: redact_text(path, sensitive_values=sensitive_values)
        for name, path in result.items()
    }
    print(json.dumps({
        "status": "PASS",
        "operation": "offline-report-regeneration",
        "database_connection_attempted": False,
        "canonical_source_mutated": False,
        "source_run": redact_text(snapshot.root, sensitive_values=sensitive_values),
        "outputs": safe,
    }, indent=2))
    return 0


def _dry_run(settings: Settings) -> int:
    validated = []
    for query in QUERIES + METADATA_QUERIES + SECURITY_METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
        validate_read_only_sql(query.sql)
        validated.append({"name": query.name, "stage": query.stage, "status": "SAFE"})
    policy = resolve_mode_policy(settings)
    configuration = {**settings.sanitized(), "resolved_mode_policy": policy.as_dict()}
    print(json.dumps({"status": "PASS", "connection_attempted": False, "queries": validated, "configuration": configuration}, indent=2))
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
        if args.command == "regenerate-reports":
            return _regenerate_reports_command(settings, args.run)
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
        if args.command in {"all", "discover-and-report"}:
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
