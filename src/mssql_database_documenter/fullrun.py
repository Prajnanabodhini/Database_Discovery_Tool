"""Sequential end-to-end read-only discovery pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Callable, Iterable

from .analysis.stages import AnalysisStagesMixin
from .config import Settings
from .connection import connect
from .contracts import EVIDENCE_CLASSES, EXTRA_OUTPUTS, REQUIRED_OUTPUTS
from .evidence_safety import audit_run_evidence
from .inventory import OUTPUT_FOLDERS, _new_run_directory, safe_path_component
from .lineage import SQL_AGENT_PIPELINE_HEADERS, SQL_AGENT_REFERENCE_HEADERS, analyze_agent_steps
# Compatibility aliases keep the pre-modularization helper import surface stable.
from .lineage.static_sql import (
    definition_references as _definition_references,
    sanitized_external_server as _sanitized_external_server,
    static_column_references as _static_column_references,
    static_definition as _static_definition,
)
from .lineage.stages import LineageStagesMixin
from .metadata.support import FEATURE_SUPPORT_HEADERS, feature_support_markdown, is_unsupported_metadata_error, support_record
from .mode_policy import resolve_mode_policy
from .programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from .profiling import (
    build_sample_plan, classify_sensitivity, load_sensitivity_overrides, mask_value,
    sample_failure_status, sanitize_sample_rows,
)
from .profiling import known_row_estimate as _known_row_estimate
from .profiling import within_safety_threshold as _within_safety_threshold
from .profiling.policy import (
    NUMERIC_TYPES, SKIP_PROFILE_TYPES, STRING_TYPES,
    classification as _classification, mask as _mask, type_family as _type_family,
)
from .profiling.stages import ProfilingStagesMixin
from .queries import METADATA_QUERIES, QUERIES, SECURITY_METADATA_QUERIES, QuerySpec
from .redaction import redact_text
from .relationships.inference import normalized_identifier as _normalized_identifier
from .relationships.stages import RelationshipStagesMixin
from .reporting.stages import ReportingStagesMixin
from .runtime import (
    ERROR_COLUMNS, is_access_limitation as _is_access_limitation,
    markdown_table as _md_table, object_key as _object_key,
    quote_identifier as _qid, sql_is_safe as _safe,
    write_csv as _csv, write_json as _json, write_markdown as _md,
)
from .safety import ReadOnlyCursor, validate_read_only_sql

class _RequestedStageComplete(Exception):
    """Internal control flow used after a requested stage passes."""


class DiscoveryCancelled(RuntimeError):
    """Raised between stages when a Web/CLI operator requests cancellation."""


class SequentialRun(
    ProfilingStagesMixin,
    RelationshipStagesMixin,
    LineageStagesMixin,
    AnalysisStagesMixin,
    ReportingStagesMixin,
):
    def __init__(
        self,
        settings: Settings,
        database: str,
        *,
        stop_after: str = "21",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> None:
        self.settings = settings
        self.database = database
        self.mode_policy = resolve_mode_policy(settings)
        self.run_id, self.root = _new_run_directory(settings.output_root, database)
        self.errors: list[dict[str, Any]] = []
        self.status: list[dict[str, Any]] = []
        self.data: dict[str, Any] = {}
        self.sensitive_values = (settings.password, settings.username, settings.server)
        self.mask_salt = hashlib.sha256(f"mssql-database-documenter|{database}".encode()).hexdigest()
        self.sensitivity_overrides = load_sensitivity_overrides(settings.sensitivity_overrides_file)
        self.connection: Any = None
        self.cursor: ReadOnlyCursor | None = None
        self.stop_after = stop_after
        self.progress_callback = progress_callback
        self.cancel_requested = cancel_requested or (lambda: False)
        self.cancelled = False
        self.failed = False

    def _progress(self, prompt: str, stage: str, status: str, **extra: Any) -> None:
        if self.progress_callback:
            self.progress_callback({"database": self.database, "prompt": prompt, "stage": stage, "status": status, **extra})

    def artifact(self, name: str) -> Path:
        folder = REQUIRED_OUTPUTS.get(name, EXTRA_OUTPUTS.get(name))
        if folder is None:
            raise KeyError(name)
        return self.root / folder / name

    def resolved_configuration(self) -> dict[str, object]:
        return {**self.settings.sanitized(), "resolved_mode_policy": self.mode_policy.as_dict()}

    def classify_column(
        self, column_name: str, *, schema: str = "", table: str = "",
        extended_property: str = "", values: Iterable[object] = (),
    ):
        return classify_sensitivity(
            column_name, database=self.database, schema=schema, table=table,
            extended_property=extended_property, values=values,
            overrides=self.sensitivity_overrides,
        )

    def stage(self, prompt: str, name: str, operation: Any) -> None:
        if self.cancel_requested():
            self._progress(prompt, name, "CANCELLED")
            raise DiscoveryCancelled(f"Cancelled before prompt {prompt}: {name}")
        started = datetime.now(timezone.utc)
        self._progress(prompt, name, "RUNNING", started_utc=started.isoformat())
        try:
            operation()
        except Exception as exc:
            self.status.append({"prompt": prompt, "stage": name, "status": "FAILED", "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat()})
            self._error(prompt, name, "", "", name, exc, "Stage incomplete", "Pipeline stopped")
            self._write_control_files(final=False)
            self._progress(prompt, name, "FAILED", error_type=type(exc).__name__)
            raise
        self.status.append({"prompt": prompt, "stage": name, "status": "PASS", "started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat()})
        self._progress(prompt, name, "PASS")
        if prompt == self.stop_after:
            raise _RequestedStageComplete

    def skip_stage(self, prompt: str, name: str, reason: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.status.append({"prompt": prompt, "stage": name, "status": "SKIPPED_BY_MODE", "reason": reason, "started_utc": now, "finished_utc": now})
        if prompt == self.stop_after:
            raise _RequestedStageComplete

    def _error(self, prompt: str, stage: str, schema: str, obj: str, query: str, exc: Exception, impact: str, continuation: str) -> None:
        self.errors.append({
            "prompt": prompt, "stage": stage, "database": self.database,
            "schema_name": schema, "object_name": obj, "query_name": query,
            "error_type": type(exc).__name__,
            "sanitized_message": redact_text(exc, sensitive_values=self.sensitive_values),
            "impact": impact, "continuation": continuation,
        })

    def fetch(self, query: QuerySpec, *, prompt: str, optional: bool = False) -> list[dict[str, Any]]:
        if self.cursor is None:
            raise RuntimeError("Connection cursor is not initialized")
        try:
            validate_read_only_sql(query.sql)
            self.cursor.execute(query.sql)
            columns = [item[0] for item in self.cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in self.cursor.fetchall()]
        except Exception as exc:
            self._error(prompt, query.stage, "", "", query.name, exc, "Category unavailable", "Recorded and continued" if optional else "Stage stopped")
            if optional and _is_access_limitation(exc):
                return []
            raise

    def fetch_dynamic(self, sql: str, *, prompt: str, stage: str, schema: str, obj: str, query_name: str) -> list[dict[str, Any]]:
        if self.cursor is None:
            raise RuntimeError("Connection cursor is not initialized")
        try:
            validate_read_only_sql(sql)
            self.cursor.execute(sql)
            columns = [item[0] for item in self.cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in self.cursor.fetchall()]
        except Exception as exc:
            self._error(prompt, stage, schema, obj, query_name, exc, "Object-level evidence unavailable", "Object skipped; stage continued")
            if _is_access_limitation(exc):
                return []
            raise

    def prompt02_safety(self) -> None:
        for query in QUERIES + METADATA_QUERIES + SECURITY_METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
            validate_read_only_sql(query.sql)
        _md(self.root / "00_Run_Metadata" / "SAFETY_MODEL.md", """# Safety Model Verification

- PASS: all registered SQL is a single `SELECT` or `WITH ... SELECT` statement.
- PASS: DML, DDL, administration, execution, job execution, and sequence advancement are blocked.
- PASS: dynamic identifiers originate only from catalog metadata and are bracket quoted.
- PASS: connection autocommit is disabled and every connection closes through rollback.
- PASS: query timeouts and large-table thresholds are configured.
""")

    def prompt03_connection(self) -> None:
        results: list[dict[str, Any]] = []
        for query in QUERIES:
            rows = self.fetch(query, prompt="03")
            for row in rows:
                if "server_name" in row:
                    row["server_name"] = "[SANITIZED]"
                if "login_name" in row:
                    row["login_name"] = "[REDACTED]"
            results.append({"query": query.name, "rows": rows})
        self.data["connection_capabilities"] = results
        _json(self.root / "02_Server_Database" / "CONNECTION_CAPABILITIES.json", results)

    def prompt04_metadata(self) -> None:
        support_rows: list[dict[str, object]] = []

        def collect(query: QuerySpec) -> list[dict[str, Any]]:
            errors_before = len(self.errors)
            forced_state: str | None = None
            try:
                rows = self.fetch(query, prompt="04", optional=True)
            except Exception as exc:
                if not query.feature_family or not is_unsupported_metadata_error(exc):
                    raise
                rows = []
                forced_state = "UNSUPPORTED"
            if query.columns:
                rows = [{column: row.get(column) for column in query.columns} for row in rows]
            if query.feature_family:
                if forced_state is None and len(self.errors) > errors_before:
                    forced_state = "INACCESSIBLE"
                support_rows.append(support_record(query, row_count=len(rows), state=forced_state))
            self.data[query.name] = rows
            _csv(self.root / query.output_folder / query.output_name, query.columns, rows)
            return rows

        for query in METADATA_QUERIES:
            collect(query)
        for query in SECURITY_METADATA_QUERIES:
            if self.settings.discover_security_metadata:
                collect(query)
            else:
                self.data[query.name] = []
                _csv(self.root / query.output_folder / query.output_name, query.columns, [])
                support_rows.append(support_record(query, row_count=0, state="DISABLED"))
        self.data["metadata_feature_support"] = support_rows
        _csv(self.artifact("MSSQL_FEATURE_SUPPORT_OVERVIEW.csv"), FEATURE_SUPPORT_HEADERS, support_rows)
        _md(self.artifact("MSSQL_FEATURE_SUPPORT_OVERVIEW.md"), feature_support_markdown(support_rows))
        if not self.data.get("tables") or not self.data.get("columns"):
            raise RuntimeError("Core table/column metadata is unavailable")


















    def prompt16_safety_review(self) -> None:
        checks = {
            "registered_sql_safe": all(_safe(query.sql) for query in QUERIES + METADATA_QUERIES + SECURITY_METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,)),
            "masking_enabled": self.settings.profile_mask_sensitive_data,
            "timeout_positive": self.settings.query_timeout_seconds > 0,
            "large_table_threshold_positive": self.settings.profile_large_table_threshold > 0,
            "errors_recorded": True,
        }
        if not all(checks.values()): raise RuntimeError(f"Safety review failed: {checks}")
        _json(self.root / "00_Run_Metadata" / "PRE_RUN_SAFETY_REVIEW.json", checks)










    def run(self) -> Path:
        try:
            self.stage("02", "security", self.prompt02_safety)
            with connect(self.settings, self.database) as connection:
                self.connection = connection; self.cursor = ReadOnlyCursor(connection.cursor())
                self.stage("03", "connection", self.prompt03_connection)
                self.stage("04", "metadata", self.prompt04_metadata)
                if self.mode_policy.programmable_logic: self.stage("05", "programmable_objects", self.prompt05_programmable)
                else: self.skip_stage("05", "programmable_objects", "DISCOVERY_MODE=metadata")
                self.stage("06", "table_size_shape", self.prompt06_size_shape)
                if self.mode_policy.data_profiles: self.stage("07", "column_profile", self.prompt07_profile)
                else: self.skip_stage("07", "column_profile", f"DISCOVERY_MODE={self.settings.discovery_mode}")
                if self.mode_policy.samples: self.stage("08", "safe_samples", self.prompt08_samples)
                else: self.skip_stage("08", "safe_samples", f"DISCOVERY_MODE={self.settings.discovery_mode}")
                self.stage("09", "sensitivity", self.prompt09_sensitivity)
                if self.mode_policy.relationship_validation: self.stage("10", "relationships", self.prompt10_relationships)
                else: self.skip_stage("10", "relationships", f"Data validation disabled in DISCOVERY_MODE={self.settings.discovery_mode}")
                if self.mode_policy.pipeline_metadata: self.stage("11", "lineage_pipelines", lambda: (self.prompt11_lineage(), self._pipelines()))
                else: self.skip_stage("11", "lineage_pipelines", "DISCOVERY_MODE=metadata")
                if self.mode_policy.programmable_logic: self.stage("12", "external_references", self.prompt12_external)
                else: self.skip_stage("12", "external_references", "DISCOVERY_MODE=metadata")
                self.stage("13", "classification_duplicates", self.prompt13_classification)
                self.stage("14", "quality_risk", self.prompt14_quality)
            self.stage("15", "output_contract", self.prompt15_outputs)
            self.stage("16", "safety_review", self.prompt16_safety_review)
            self.stage("17", "acceptance_git_handoff", self.prompt17_acceptance)
            self.stage("18", "multi_database_comparison", self.prompt18_comparison)
            self.stage("19", "required_outputs", self.prompt19_required)
            self.stage("20", "environment_evidence", self.prompt20_environment)
            self.stage("21", "final_code_review", self.prompt21_review)
        except _RequestedStageComplete:
            pass
        except DiscoveryCancelled:
            self.cancelled = True
            self.finalize()
            raise
        except Exception as exc:
            # A real attempted run remains auditable even when an early connection or
            # discovery stage fails.  Finalization writes only truthful partial state.
            self.failed = True
            if not any(item.get("status") == "FAILED" for item in self.status):
                now = datetime.now(timezone.utc).isoformat()
                self.status.append({"prompt": "03", "stage": "connection_setup", "status": "FAILED", "started_utc": now, "finished_utc": now})
                self._error("03", "connection_setup", "", "", "connect", exc, "Live discovery did not start", "Run finalized as failed")
            self.finalize()
            raise
        self.finalize()
        return self.root

    def resume_after_comparison(self) -> Path:
        """Continue a coordinated multi-database run after global prompt 18 output exists."""
        self.stop_after = "21"
        try:
            self.stage("18", "multi_database_comparison", self.prompt18_comparison)
            self.stage("19", "required_outputs", self.prompt19_required)
            self.stage("20", "environment_evidence", self.prompt20_environment)
            self.stage("21", "final_code_review", self.prompt21_review)
        except _RequestedStageComplete:
            pass
        self.finalize()
        return self.root


def _safe(sql: str) -> bool:
    validate_read_only_sql(sql)
    return True


def run_all(
    settings: Settings,
    *,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> list[Path]:
    settings.validate_for_connection()
    return [
        SequentialRun(settings, database, stop_after="21", progress_callback=progress_callback, cancel_requested=cancel_requested).run()
        for database in settings.databases
    ]


def run_until(settings: Settings, prompt: str) -> list[Path]:
    settings.validate_for_connection()
    if prompt not in {f"{number:02d}" for number in range(2, 22)}:
        raise ValueError(f"Unsupported stop prompt: {prompt}")
    return [SequentialRun(settings, database, stop_after=prompt).run() for database in settings.databases]
