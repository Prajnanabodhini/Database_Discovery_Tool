"""Environment-backed configuration with secret-safe diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import os
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when required or invalid configuration is encountered."""


TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
FALSE_VALUES = frozenset({"0", "false", "no", "off"})
VALID_MODES = frozenset({"metadata", "metadata+logic", "safe-profile", "full-readonly"})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _parse_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ConfigurationError(f"{name} must be true/false, yes/no, on/off, or 1/0")


def _parse_int(value: str, name: str, *, minimum: int = 0) -> int:
    try:
        result = int(value.strip())
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if result < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}")
    return result


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read a small, predictable dotenv subset without requiring dependencies."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Invalid .env line {line_number}: expected NAME=value")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _get(source: Mapping[str, str], name: str, default: str = "") -> str:
    value = source.get(name, default)
    return value if value is not None else default


@dataclass(frozen=True, slots=True)
class Settings:
    server: str = ""
    databases: tuple[str, ...] = ()
    driver: str = "ODBC Driver 18 for SQL Server"
    trusted_connection: bool = True
    username: str = ""
    password: str = ""
    encrypt: bool = False
    trust_server_certificate: bool = True
    query_timeout_seconds: int = 60
    discovery_mode: str = "metadata+logic"
    profile_sample_rows: int = 100
    profile_include_sample_data: bool = True
    profile_mask_sensitive_data: bool = True
    profile_exact_row_counts: bool = False
    profile_exact_row_count_threshold: int = 100_000
    profile_distinct_values: bool = True
    profile_max_distinct_values: int = 50
    profile_large_table_threshold: int = 1_000_000
    discover_sql_agent_jobs: bool = True
    output_root: Path = Path("output")
    git_export_root: Path = Path("git_export")
    sanitize_server_name: bool = True
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    web_auto_open_browser: bool = True
    max_concurrent_discovery_jobs: int = 1
    enable_three_run_comparison: bool = True

    @classmethod
    def from_environment(
        cls,
        *,
        env: Mapping[str, str] | None = None,
        dotenv_path: Path | None = Path(".env"),
    ) -> "Settings":
        merged = dict(_read_dotenv(dotenv_path)) if dotenv_path else {}
        merged.update(dict(os.environ if env is None else env))

        database_list = [item.strip() for item in _get(merged, "MSSQL_DATABASES").split(",") if item.strip()]
        single_database = _get(merged, "MSSQL_DATABASE").strip()
        if single_database and database_list:
            raise ConfigurationError("Set MSSQL_DATABASE or MSSQL_DATABASES, not both")
        databases = tuple(database_list or ([single_database] if single_database else []))
        if len(databases) != len(set(name.casefold() for name in databases)):
            raise ConfigurationError("Configured database names must be unique")

        mode = _get(merged, "DISCOVERY_MODE", "metadata+logic").strip().lower()
        if mode not in VALID_MODES:
            raise ConfigurationError(f"DISCOVERY_MODE must be one of: {', '.join(sorted(VALID_MODES))}")

        return cls(
            server=_get(merged, "MSSQL_SERVER").strip(),
            databases=databases,
            driver=_get(merged, "MSSQL_DRIVER", "ODBC Driver 18 for SQL Server").strip(),
            trusted_connection=_parse_bool(_get(merged, "MSSQL_TRUSTED_CONNECTION", "true"), "MSSQL_TRUSTED_CONNECTION"),
            username=_get(merged, "MSSQL_USERNAME").strip(),
            password=_get(merged, "MSSQL_PASSWORD"),
            encrypt=_parse_bool(_get(merged, "MSSQL_ENCRYPT", "no"), "MSSQL_ENCRYPT"),
            trust_server_certificate=_parse_bool(_get(merged, "MSSQL_TRUST_SERVER_CERTIFICATE", "yes"), "MSSQL_TRUST_SERVER_CERTIFICATE"),
            query_timeout_seconds=_parse_int(_get(merged, "MSSQL_QUERY_TIMEOUT_SECONDS", "60"), "MSSQL_QUERY_TIMEOUT_SECONDS", minimum=1),
            discovery_mode=mode,
            profile_sample_rows=_parse_int(_get(merged, "PROFILE_SAMPLE_ROWS", "100"), "PROFILE_SAMPLE_ROWS"),
            profile_include_sample_data=_parse_bool(_get(merged, "PROFILE_INCLUDE_SAMPLE_DATA", "true"), "PROFILE_INCLUDE_SAMPLE_DATA"),
            profile_mask_sensitive_data=_parse_bool(_get(merged, "PROFILE_MASK_SENSITIVE_DATA", "true"), "PROFILE_MASK_SENSITIVE_DATA"),
            profile_exact_row_counts=_parse_bool(_get(merged, "PROFILE_EXACT_ROW_COUNTS", "false"), "PROFILE_EXACT_ROW_COUNTS"),
            profile_exact_row_count_threshold=_parse_int(_get(merged, "PROFILE_EXACT_ROW_COUNT_THRESHOLD", "100000"), "PROFILE_EXACT_ROW_COUNT_THRESHOLD", minimum=1),
            profile_distinct_values=_parse_bool(_get(merged, "PROFILE_DISTINCT_VALUES", "true"), "PROFILE_DISTINCT_VALUES"),
            profile_max_distinct_values=_parse_int(_get(merged, "PROFILE_MAX_DISTINCT_VALUES", "50"), "PROFILE_MAX_DISTINCT_VALUES", minimum=1),
            profile_large_table_threshold=_parse_int(_get(merged, "PROFILE_LARGE_TABLE_THRESHOLD", "1000000"), "PROFILE_LARGE_TABLE_THRESHOLD", minimum=1),
            discover_sql_agent_jobs=_parse_bool(_get(merged, "DISCOVER_SQL_AGENT_JOBS", "true"), "DISCOVER_SQL_AGENT_JOBS"),
            output_root=Path(_get(merged, "OUTPUT_ROOT", "output")),
            git_export_root=Path(_get(merged, "GIT_EXPORT_ROOT", "git_export")),
            sanitize_server_name=_parse_bool(_get(merged, "SANITIZE_SERVER_NAME", "true"), "SANITIZE_SERVER_NAME"),
            web_host=_get(merged, "WEB_HOST", "127.0.0.1").strip(),
            web_port=_parse_int(_get(merged, "WEB_PORT", "8765"), "WEB_PORT", minimum=1),
            web_auto_open_browser=_parse_bool(_get(merged, "WEB_AUTO_OPEN_BROWSER", "true"), "WEB_AUTO_OPEN_BROWSER"),
            max_concurrent_discovery_jobs=_parse_int(_get(merged, "MAX_CONCURRENT_DISCOVERY_JOBS", "1"), "MAX_CONCURRENT_DISCOVERY_JOBS", minimum=1),
            enable_three_run_comparison=_parse_bool(_get(merged, "ENABLE_THREE_RUN_COMPARISON", "true"), "ENABLE_THREE_RUN_COMPARISON"),
        )

    def with_database_override(self, database: str | None) -> "Settings":
        if database is None:
            return self
        clean = database.strip()
        if not clean:
            raise ConfigurationError("--database cannot be empty")
        return replace(self, databases=(clean,))

    def with_mode_override(self, mode: str | None) -> "Settings":
        if mode is None:
            return self
        normalized = mode.strip().lower()
        if normalized not in VALID_MODES:
            raise ConfigurationError(f"--mode must be one of: {', '.join(sorted(VALID_MODES))}")
        return replace(self, discovery_mode=normalized)

    def validate_for_connection(self) -> None:
        if not self.server:
            raise ConfigurationError("MSSQL_SERVER is required for a live connection")
        if not self.databases:
            raise ConfigurationError("MSSQL_DATABASE or MSSQL_DATABASES is required for a live connection")
        if not self.driver:
            raise ConfigurationError("MSSQL_DRIVER is required for a live connection")
        if self.trusted_connection:
            if self.username or self.password:
                raise ConfigurationError("Do not set SQL credentials when MSSQL_TRUSTED_CONNECTION=true")
        elif not self.username or not self.password:
            raise ConfigurationError("MSSQL_USERNAME and MSSQL_PASSWORD are required for SQL authentication")

    def validate_for_web(self) -> None:
        if self.web_host.casefold() not in LOOPBACK_HOSTS:
            raise ConfigurationError("WEB_HOST must be a loopback host (127.0.0.1, localhost, or ::1)")
        if self.web_port > 65535:
            raise ConfigurationError("WEB_PORT must be between 1 and 65535")
        if self.max_concurrent_discovery_jobs != 1:
            raise ConfigurationError("v3 permits exactly one concurrent discovery job per configured server")

    def sanitized(self) -> dict[str, object]:
        server = "[SANITIZED]" if self.server and self.sanitize_server_name else self.server
        return {
            "server": server or "[NOT CONFIGURED]",
            "databases": list(self.databases),
            "driver": self.driver,
            "trusted_connection": self.trusted_connection,
            "username": "[REDACTED]" if self.username else "[NOT SET]",
            "password": "[REDACTED]" if self.password else "[NOT SET]",
            "encrypt": self.encrypt,
            "trust_server_certificate": self.trust_server_certificate,
            "query_timeout_seconds": self.query_timeout_seconds,
            "discovery_mode": self.discovery_mode,
            "profile_include_sample_data": self.profile_include_sample_data,
            "profile_mask_sensitive_data": self.profile_mask_sensitive_data,
            "profile_sample_rows": self.profile_sample_rows,
            "profile_exact_row_counts": self.profile_exact_row_counts,
            "profile_exact_row_count_threshold": self.profile_exact_row_count_threshold,
            "profile_distinct_values": self.profile_distinct_values,
            "profile_max_distinct_values": self.profile_max_distinct_values,
            "profile_large_table_threshold": self.profile_large_table_threshold,
            "discover_sql_agent_jobs": self.discover_sql_agent_jobs,
            "output_root": str(self.output_root),
            "git_export_root": str(self.git_export_root),
            "sanitize_server_name": self.sanitize_server_name,
            "web_host": self.web_host,
            "web_port": self.web_port,
            "web_auto_open_browser": self.web_auto_open_browser,
            "max_concurrent_discovery_jobs": self.max_concurrent_discovery_jobs,
            "enable_three_run_comparison": self.enable_three_run_comparison,
        }
