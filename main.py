"""Canonical launcher for the local Web UI and read-only CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only MSSQL documentation dashboard")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    commands = parser.add_subparsers(dest="command")
    web = commands.add_parser("web", help="Launch the localhost-only dashboard")
    web.add_argument("--no-browser", action="store_true", help="Do not open the system browser")
    commands.add_parser("test-connection", help="Run the safe console connection check")
    cli = commands.add_parser("cli", help="Run a predefined discovery mode from the console")
    cli.add_argument("--mode", required=True, choices=("metadata", "metadata+logic", "safe-profile", "full-readonly"))
    cli.add_argument("--database", help="Use one explicitly configured database")
    cli.add_argument("--action", choices=("all", "report"), default="all")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = args.command or "web"
    if command == "web":
        from mssql_database_documenter.web.app import run_web

        return run_web(args.env_file, auto_open=not getattr(args, "no_browser", False))
    from mssql_database_documenter.cli import main as cli_main
    if command == "test-connection":
        return cli_main(["--env-file", str(args.env_file), "test-connection"])
    forwarded = ["--env-file", str(args.env_file), "--mode", args.mode]
    if args.database:
        forwarded.extend(("--database", args.database))
    forwarded.append(args.action)
    return cli_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
