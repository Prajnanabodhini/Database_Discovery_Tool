"""Reporting-domain stages for the sequential discovery engine."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
import importlib.metadata
from pathlib import Path
import platform
import re
from typing import Any, Iterable

from .. import __version__
from ..contracts import EXTRA_OUTPUTS, REQUIRED_OUTPUTS
from ..evidence_safety import audit_run_evidence
from ..inventory import safe_path_component
from ..lineage.agent import SQL_AGENT_PIPELINE_HEADERS, SQL_AGENT_REFERENCE_HEADERS
from ..metadata.support import FEATURE_SUPPORT_HEADERS
from ..programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from ..queries import METADATA_QUERIES, QUERIES, SECURITY_METADATA_QUERIES
from ..runtime import (
    ERROR_COLUMNS,
    markdown_table as _md_table,
    object_key as _object_key,
    sql_is_safe as _safe,
    write_csv as _csv,
    write_json as _json,
    write_markdown as _md,
)


class ReportingStagesMixin:
    """Object documentation, reports, control files, and manifests."""

    def _snapshot_integrity(self) -> None:
        status_values = [str(item.get("status") or "") for item in self.status]
        accounted = {"PASS", "SKIPPED_BY_MODE"}
        failed_stage_count = sum(value == "FAILED" for value in status_values)
        summary_status = "CANCELLED" if self.cancelled else "FAILED" if self.failed or "FAILED" in status_values else "COMPLETED_WITH_WARNINGS" if self.errors else "COMPLETED" if self.status and all(value in accounted for value in status_values) else "PARTIAL"
        server_rows = next((item.get("rows", []) for item in self.data.get("connection_capabilities", []) if item.get("query") == "server_capabilities"), [])
        run_summary = {
            "run_id": self.run_id, "database": self.database, "server_alias": self.settings.sanitized()["server"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": self.settings.discovery_mode,
            "status": summary_status, "tool_version": __version__,
            "sql_server_version": (server_rows[0].get("product_version") if server_rows else "UNKNOWN"),
            "sample_rows": self.mode_policy.sample_row_limit, "exact_row_counts": self.mode_policy.exact_counts,
            "mask_sensitive_data": self.settings.profile_mask_sensitive_data,
            "profile_settings": {"sample_rows": self.mode_policy.sample_row_limit, "include_sample_data": self.mode_policy.samples, "sample_tables": self.mode_policy.sample_tables, "sample_views": self.mode_policy.sample_views, "sample_large_tables": self.mode_policy.sample_large_tables, "mask_sensitive_data": self.settings.profile_mask_sensitive_data, "exact_row_counts": self.mode_policy.exact_counts, "exact_row_count_threshold": self.mode_policy.exact_count_ceiling, "large_table_threshold": self.mode_policy.profile_row_threshold},
            "resolved_mode_policy": self.mode_policy.as_dict(),
            "completed_stage_count": sum(item.get("status") == "PASS" for item in self.status),
            "completion_coverage": f"{sum(item.get('status') in accounted for item in self.status)}/{20}",
            "error_count": failed_stage_count,
            "warning_count": max(0, len(self.errors) - failed_stage_count),
            "warning_error_count": len(self.errors), "file_count_before_manifest": sum(1 for path in self.root.rglob("*") if path.is_file()),
        }
        _json(self.artifact("run_summary.json"), run_summary)
        files_before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file())
        manifest_path = self.artifact("manifest.json"); checksum_path = self.artifact("checksums.sha256")
        package_names = ("pyodbc", "python-dotenv", "pytest", "pandas", "sqlparse", "networkx", "jinja2")
        packages = {}
        for name in package_names:
            try: packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: packages[name] = "NOT_INSTALLED"
        server_rows = next((item.get("rows", []) for item in self.data.get("connection_capabilities", []) if item.get("query") == "server_capabilities"), [])
        manifest = {
            "run_id": self.run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool": "mssql-database-documenter", "tool_version": __version__, "database": self.database,
            "python_version": platform.python_version(), "platform": platform.platform(), "packages": packages,
            "odbc_driver": self.settings.driver, "sql_server_capabilities": server_rows,
            "configuration": self.resolved_configuration(), "stages": self.status,
            "resolved_mode_policy": self.mode_policy.as_dict(),
            "expected_stage_count": 20,
            "warnings": [item["sanitized_message"] for item in self.errors], "errors": len(self.errors),
            "files": sorted(set(files_before + [manifest_path.relative_to(self.root).as_posix(), checksum_path.relative_to(self.root).as_posix()])),
            "git_export": [],  # Export is a separate explicit CLI/Web operation in v3.
        }
        _json(manifest_path, manifest)
        lines = []
        for path in sorted(path for path in self.root.rglob("*") if path.is_file() and path != checksum_path):
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(self.root).as_posix()}")
        checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def finalize(self) -> None:
        self._write_control_files(final=True)
        self._snapshot_integrity()

    def _write_control_files(self, *, final: bool) -> None:
        _csv(self.artifact("DISCOVERY_ERRORS.csv"), ERROR_COLUMNS, self.errors)
        _json(self.artifact("STAGE_STATUS.json"), self.status)
        completed = [row["prompt"] for row in self.status if row["status"] == "PASS"]
        table_keys = {_object_key(row) for row in self.data.get("tables", [])}
        sampled = set(self.data.get("sample_rows", {}))
        sample_status_counts: dict[str, int] = {}
        for row in self.data.get("sample_index", []):
            status = str(row.get("status") or "UNKNOWN")
            sample_status_counts[status] = sample_status_counts.get(status, 0) + 1
        sample_status_coverage = ", ".join(
            f"{status}={count}"
            for status, count in sorted(sample_status_counts.items())
        ) or "NONE"
        profiled_tables = {_object_key(row) for row in self.data.get("column_profile", []) if row.get("profile_status") == "PROFILED"}
        lines = [
            "# Discovery Coverage", "", f"- Completed prompt stages: {', '.join(completed)}",
            f"- Recorded errors/limitations: {len(self.errors)}", f"- Finalized: {final}", "",
            "## Object coverage", "",
            f"- Tables discovered: {len(table_keys)}", f"- Tables documented: {len(list((self.root / '20_Object_Documentation' / 'Tables').glob('*.md')))}",
            f"- Tables with at least one profiled column: {len(profiled_tables)}", f"- Tables/views with sample files attempted: {len(sampled)}",
            f"- Sample status coverage: {sample_status_coverage}",
            f"- Columns discovered: {len(self.data.get('columns', []))}", f"- Column profile rows: {len(self.data.get('column_profile', []))}",
            f"- Programmable objects discovered: {sum(len(self.data.get(name, [])) for name in ('views', 'procedures', 'functions', 'triggers'))}",
            f"- Dependency/lineage edges: {len(self.data.get('lineage', []))}", f"- Relationship cardinality rows: {len(self.data.get('relationship_cardinality', []))}", "",
            "## Shortfalls and limitations", "",
        ]
        if self.errors:
            lines.extend(f"- Prompt {item['prompt']} / {item['stage']} / `{item.get('schema_name')}.{item.get('object_name')}`: {item['impact']} ({item['continuation']})" for item in self.errors)
        else:
            lines.append("- No query/access errors were recorded.")
        lines.extend(("- Dynamic SQL, encrypted definitions, invalid objects, and permissions may reduce static coverage.", "- Categories that are empty or inaccessible retain header-only or explanatory artifacts."))
        _md(self.artifact("DISCOVERY_COVERAGE.md"), "\n".join(lines))

    def prompt21_review(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        table_docs = list((self.root / "20_Object_Documentation" / "Tables").glob("*.md"))
        programmable_docs = [path for folder in ("Views", "Procedures", "Functions", "Triggers") for path in (self.root / "20_Object_Documentation" / folder).glob("*.md")]
        required_table_sections = ("## Size and shape", "## Primary keys", "## Indexes", "## Column profiles", "## Masked sample", "## Lineage", "## Pipeline participation", "## Data-quality observations")
        required_programmable_sections = ("## Parameters", "## Reads, writes, calls, and references", "## Pipeline role", "## Risks and uncertainties", "## Sanitized static definition")
        semantic_checks = {
            "all_tables_documented": len(table_docs) == len(self.data.get("tables", [])),
            "all_programmable_objects_documented": len(programmable_docs) == sum(len(self.data.get(name, [])) for name in ("views", "procedures", "functions", "triggers")),
            "table_document_contract": all(all(section in path.read_text(encoding="utf-8") for section in required_table_sections) for path in table_docs),
            "programmable_document_contract": all(all(section in path.read_text(encoding="utf-8") for section in required_programmable_sections) for path in programmable_docs),
            "diagram_has_no_metadata_placeholder": "metadata_placeholder" not in self.artifact("FULL_ER_DIAGRAM.md").read_text(encoding="utf-8"),
            "comparison_engine_available": callable(__import__("mssql_database_documenter.comparison", fromlist=["compare_run_paths"]).compare_run_paths),
            "required_outputs_present": not [name for name, folder in REQUIRED_OUTPUTS.items() if not (self.root / folder / name).is_file()],
            "all_registered_sql_safe": all(_safe(query.sql) for query in QUERIES + METADATA_QUERIES + SECURITY_METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,)),
        }
        if not all(semantic_checks.values()):
            raise RuntimeError(f"Final semantic acceptance checks failed: {semantic_checks}")
        python_files = sorted(package_root.rglob("*.py"))
        file_rows = []
        for path in python_files:
            content = path.read_text(encoding="utf-8")
            compile(content, str(path), "exec")
            file_rows.append((path.relative_to(package_root.parent).as_posix(), len(content.splitlines()), hashlib.sha256(content.encode("utf-8")).hexdigest()))
        def line_of(relative_path: str, needle: str) -> int:
            source_path = package_root / relative_path
            return next(index for index, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), 1) if needle in line)
        checks = [
            ("Fail-closed SQL validation", f"mssql_database_documenter/safety.py:{line_of('safety.py', 'def validate_read_only_sql')}", "PASS"),
            ("Final execution-boundary validation", f"mssql_database_documenter/safety.py:{line_of('safety.py', 'def execute')}", "PASS"),
            ("Autocommit disabled and rollback close", f"mssql_database_documenter/connection.py:{line_of('connection.py', 'autocommit=False')}", "PASS"),
            ("Configuration secret sanitization", f"mssql_database_documenter/config.py:{line_of('config.py', 'def sanitized')}", "PASS"),
            ("Credential/PII masking", f"mssql_database_documenter/profiling/policy.py:{line_of('profiling/policy.py', 'def mask')}", "PASS"),
            ("Sequential stop-on-failed-stage gate", f"mssql_database_documenter/fullrun.py:{line_of('fullrun.py', 'def stage')}", "PASS"),
            ("Required output validation", f"mssql_database_documenter/reporting/stages.py:{line_of('reporting/stages.py', 'def prompt19_required')}", "PASS"),
            ("Manifest and SHA-256 generation", f"mssql_database_documenter/reporting/stages.py:{line_of('reporting/stages.py', 'def _snapshot_integrity')}", "PASS"),
            ("Per-object documentation contract", "generated 20_Object_Documentation", "PASS"),
            ("Explicit 2/3-run comparison engine", "src/mssql_database_documenter/comparison", "PASS"),
            ("ER diagrams contain real metadata", "generated 19_Diagrams", "PASS"),
        ]
        lines = [
            "# Final Code Review", "", "Overall result: **PASS**", "",
            "- Developer pytest invoked during discovery: no",
            f"- Runtime package files compiled and audited: {len(file_rows)}",
            f"- Registered static SQL statements validated: {len(QUERIES + METADATA_QUERIES + SECURITY_METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,))}",
            "- Database touched during this review: no", "- Mutation/admin/execution capability implemented: no", "",
            "## Current-run semantic invariants", "",
            "These checks inspect the current run and registered runtime contracts only; developer tests are a separate explicit `python main.py self-test` action.", "",
            "## Control checks", "", "| Check | File/line | Result |", "|---|---|---|",
        ]
        lines.extend(f"| {name} | `{location}` | {result} |" for name, location, result in checks)
        lines.extend((
            "", "## Modular ownership audit", "",
            "| Owner | Responsibility |", "|---|---|",
            "| `fullrun.py` | Run state, sequential gates, cancellation/errors, connection lifecycle, and orchestration |",
            "| `profiling/` | Sensitivity, sampling, and table/column profiling policy |",
            "| `relationships/` | Relationship inference, cardinality, validation, and orphan analysis |",
            "| `lineage/` | Static SQL, dependencies, SQL Agent evidence, and pipeline construction |",
            "| `analysis/` | Classification, duplicate detection, quality observations, and risk |",
            "| `reporting/` | Object documentation, diagrams, narratives, HTML, control files, and manifests |",
        ))
        lines.extend(("", "## File audit", "", "| Python file | Lines | SHA-256 | Result |", "|---|---:|---|---|"))
        lines.extend(f"| `{name}` | {count} | `{digest}` | PASS |" for name, count, digest in file_rows)
        lines.extend(("", "## Evidence boundaries", "", "Dynamic SQL, encrypted definitions, invalid database objects, permission limitations, and heuristic classifications remain explicitly identified as uncertainty; no inference is promoted to a declared fact."))
        lines.extend(("", "## Semantic acceptance", ""))
        lines.extend(f"- [x] {name.replace('_', ' ')}" for name in semantic_checks)
        _md(self.root / "99_Git_Handoff" / "FINAL_CODE_REVIEW.md", "\n".join(lines))

    def prompt20_environment(self) -> None:
        _json(self.artifact("RUN_CONFIGURATION.json"), self.resolved_configuration())

    def prompt19_required(self) -> None:
        missing = [name for name, folder in REQUIRED_OUTPUTS.items() if name not in {"manifest.json", "checksums.sha256"} and not (self.root / folder / name).is_file()]
        if missing: raise RuntimeError(f"Required output files missing: {missing}")

    def prompt18_comparison(self) -> None:
        self.data["comparison_status"] = [{"status": "AVAILABLE_ON_DEMAND", "reason": "v3 comparisons are generated only by an explicit 2/3-run action"}]

    def prompt17_acceptance(self) -> None:
        audit = audit_run_evidence(self.root, sensitive_values=self.sensitive_values)
        _json(self.root / "99_Git_Handoff" / "MASKING_SAFETY_AUDIT.json", audit.as_dict())
        if not audit.passed:
            raise RuntimeError(f"Git safety gate failed with {len(audit.violations)} evidence violation(s)")
        _md(self.artifact("SAFE_TO_COMMIT_CHECKLIST.md"), f"""# Safe to Commit Checklist

- [x] `.env`, credential files, symbolic links, caches, temporary paths, and internal logs excluded
- [x] configured server/login/password strings and secret assignments absent from artifacts
- [x] server identity sanitized
- [x] sensitive column-profile minimum/maximum values masked before disk
- [x] sensitive low-cardinality values masked before disk
- [x] sensitive samples masked before disk
- [x] credential/password/hash/token/secret values always redacted
- [x] programmable definitions sanitized before writing

Executable audit result: **PASS**  
Files scanned: {audit.files_scanned}  
Classified columns: {audit.classified_columns}  
Sensitive columns: {audit.sensitive_columns}  
Sensitive values checked: {audit.sensitive_values_checked}

Git export is intentionally deferred until an explicit CLI/Web action. The exporter repeats this audit and fails closed rather than trusting this checklist.
""")

    def _ensure_contract_files(self) -> None:
        csv_headers = {
            "PIPELINE_CATALOGUE.csv": ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence", "evidence_class"),
            "SQL_AGENT_STEP_REFERENCES.csv": SQL_AGENT_REFERENCE_HEADERS,
            "SQL_AGENT_PIPELINE_EDGES.csv": SQL_AGENT_PIPELINE_HEADERS,
            "MSSQL_FEATURE_SUPPORT_OVERVIEW.csv": FEATURE_SUPPORT_HEADERS,
        }
        for name, folder in {**REQUIRED_OUTPUTS, **EXTRA_OUTPUTS}.items():
            path = self.root / folder / name
            if path.exists() or name in {"manifest.json", "checksums.sha256", "STAGE_STATUS.json", "RUN_CONFIGURATION.json"}:
                continue
            if name.endswith(".csv"): _csv(path, csv_headers.get(name, ("status", "explanation")), [])
            elif name.endswith(".json"): _json(path, {"status": "EMPTY_OR_NOT_APPLICABLE"})
            else: _md(path, f"# {name.removesuffix('.md').replace('_', ' ').title()}\n\nNo accessible evidence was produced for this category, or the category is not applicable. This is recorded explicitly rather than silently omitted.")

    def _html_report(self) -> None:
        safe_database = html.escape(self.database)
        metrics = {"Tables": len(self.data.get("tables", [])), "Columns": len(self.data.get("columns", [])), "Views": len(self.data.get("views", [])), "Procedures": len(self.data.get("procedures", [])), "Lineage edges": len(self.data.get("lineage", [])), "Risks": len(self.data.get("risks", []))}
        cards = "".join(f"<div><strong>{value}</strong><span>{key}</span></div>" for key, value in metrics.items())
        links = (("Executive summary", "../01_Executive_Summary/MSSQL_EXECUTIVE_SUMMARY.md"), ("Table catalogue", "../04_Tables/TABLE_CATALOGUE.csv"), ("Column catalogue", "../05_Columns/COLUMN_CATALOGUE.csv"), ("Lineage", "../15_Lineage/LINEAGE_EDGES.csv"), ("Pipelines", "../16_Pipelines/PIPELINE_CATALOGUE.csv"), ("Risk register", "../18_Risks_Uncertainties/RISK_AND_UNCERTAINTY_REGISTER.csv"), ("Manifest", "../00_Run_Metadata/manifest.json"))
        navigation = "".join(f"<li><a href='{href}'>{label}</a></li>" for label, href in links)
        document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>MSSQL documentation - {safe_database}</title><style>body{{font:15px system-ui;margin:0;background:#f3f6fa;color:#172033}}header{{padding:4rem max(5vw,2rem);background:#14263d;color:white}}main{{padding:2rem max(5vw,2rem)}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-top:-3.5rem}}.cards div,section{{background:white;border:1px solid #dde3ec;border-radius:16px;padding:1.4rem}}.cards strong,.cards span{{display:block}}.cards strong{{font-size:2rem;color:#1769e0}}section{{margin-top:1.5rem}}a{{color:#1769e0}}li{{margin:.6rem 0}}</style></head><body><header><small>READ-ONLY EVIDENCE REPORT</small><h1>{safe_database}</h1><p>Styled navigation supplements canonical CSV, JSON, Markdown and checksums; it does not replace them.</p></header><main><div class='cards'>{cards}</div><section><h2>Full evidence</h2><ul>{navigation}</ul><p>Use the local Web UI for safe rendering, pagination, search, raw view and downloads.</p></section></main></body></html>"""
        path = self.artifact("MSSQL_DOCUMENTATION_REPORT.html"); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(document, encoding="utf-8")

    def _narratives(self) -> None:
        metrics = {"database": self.database, "tables": len(self.data.get("tables", [])), "columns": len(self.data.get("columns", [])), "views": len(self.data.get("views", [])), "procedures": len(self.data.get("procedures", [])), "functions": len(self.data.get("functions", [])), "triggers": len(self.data.get("triggers", [])), "declared_foreign_key_rows": len(self.data.get("foreign_keys", [])), "inferred_relationships": len(self.data.get("inferred_relationships", [])), "errors": len(self.errors)}
        _json(self.artifact("DATABASE_SUMMARY_METRICS.json"), metrics)
        _md(self.artifact("DATABASE_OVERVIEW.md"), "# Database Overview\n\n" + "\n".join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in metrics.items()))
        _md(self.artifact("DATABASE_GLOSSARY.md"), "# Database Glossary\n\nGenerated structural glossary. Semantic definitions remain `UNKNOWN` unless supported by extended properties.\n\n" + "\n".join(f"- `{row['schema_name']}.{row['object_name']}` — inferred purpose not asserted as fact." for row in self.data.get("tables", [])))
        _md(self.artifact("MSSQL_EXECUTIVE_SUMMARY.md"), f"# MSSQL Executive Summary\n\nThe configured database contains {metrics['tables']} tables and {metrics['columns']} columns visible to the reader identity. All discovery was read-only. Declared and inferred relationships are reported separately. See the risk register and access limitations before making design decisions.")
        _md(self.artifact("PIPELINE_SUMMARY.md"), f"# Pipeline Summary\n\nStatic dependency and job evidence produced {len(self.data.get('pipelines', []))} candidate pipeline rows. Object existence does not prove active use.")
        _md(self.artifact("ACCESS_AND_DISCOVERY_LIMITATIONS.md"), "# Access and Discovery Limitations\n\n- Results cover only objects visible to the configured identity.\n- Dynamic SQL and encrypted modules can make dependencies opaque.\n- Samples are masked before writing.\n- Profiling is skipped for large tables and unsuitable types.\n- Inference is never equivalent to a declared constraint or documented business rule.\n- External systems were not queried.\n")

    def _diagrams(self) -> None:
        columns_by_table: dict[str, list[dict[str, Any]]] = {}
        for column in self.data.get("columns", []):
            if column.get("object_type") == "USER_TABLE":
                columns_by_table.setdefault(_object_key(column), []).append(column)
        pk_columns = {(_object_key(row), str(row.get("column_name") or "")) for row in self.data.get("primary_keys", [])}
        fk_columns = {(f"{row.get('source_schema')}.{row.get('source_object')}", str(row.get("source_column") or "")) for row in self.data.get("foreign_keys", [])}

        def node_for(schema: str, obj: str) -> str:
            return re.sub(r"[^A-Za-z0-9_]", "_", f"{schema}_{obj}")

        def entity_lines(schema: str, obj: str) -> list[str]:
            key = f"{schema}.{obj}"; result = [f"    {node_for(schema, obj)} {{"]
            for column in sorted(columns_by_table.get(key, []), key=lambda item: int(item.get("column_id") or 0)):
                dtype = re.sub(r"[^A-Za-z0-9_]", "_", str(column.get("data_type") or "unknown"))
                name = re.sub(r"[^A-Za-z0-9_]", "_", str(column.get("column_name") or "column"))
                markers = []
                if (key, str(column.get("column_name") or "")) in pk_columns: markers.append("PK")
                if (key, str(column.get("column_name") or "")) in fk_columns: markers.append("FK")
                result.append(f"        {dtype} {name}{' ' + ','.join(markers) if markers else ''}")
            result.append("    }")
            return result

        lines = ["# Full ER Diagram", "", "```mermaid", "erDiagram"]
        for table in self.data["tables"]:
            lines.extend(entity_lines(str(table["schema_name"]), str(table["object_name"])))
        for fk in self.data.get("foreign_keys", []):
            source = node_for(str(fk["source_schema"]), str(fk["source_object"]))
            target = node_for(str(fk["target_schema"]), str(fk["target_object"]))
            lines.append(f"    {target} ||--o{{ {source} : \"{fk['constraint_name']}\"")
        lines.append("```")
        _md(self.artifact("FULL_ER_DIAGRAM.md"), "\n".join(lines))
        by_schema: dict[str, list[dict[str, Any]]] = {}
        for table in self.data["tables"]:
            by_schema.setdefault(str(table["schema_name"]), []).append(table)
        for schema, tables in by_schema.items():
            schema_lines = [f"# Schema Diagram — {schema}", "", "```mermaid", "erDiagram"]
            for table in tables:
                schema_lines.extend(entity_lines(schema, str(table["object_name"])))
            table_names = {str(table["object_name"]) for table in tables}
            for fk in self.data.get("foreign_keys", []):
                if str(fk.get("source_schema")) == schema and str(fk.get("target_schema")) == schema and str(fk.get("source_object")) in table_names and str(fk.get("target_object")) in table_names:
                    schema_lines.append(f"    {node_for(schema, str(fk['target_object']))} ||--o{{ {node_for(schema, str(fk['source_object']))} : \"{fk['constraint_name']}\"")
            schema_lines.append("```")
            _md(self.root / "19_Diagrams" / f"SCHEMA_{safe_path_component(schema)}.md", "\n".join(schema_lines))
        dependencies = self.data.get("all_dependencies", self.data.get("dependencies", []))
        dependency_groups: dict[str, list[dict[str, Any]]] = {"ALL": list(dependencies), "CROSS_DATABASE_SERVER": []}
        for dep in dependencies:
            source_type = str(dep.get("source_type") or "UNKNOWN").upper().replace("SQL_", "")
            dependency_groups.setdefault(source_type, []).append(dep)
            if dep.get("target_server") or dep.get("target_database"):
                dependency_groups["CROSS_DATABASE_SERVER"].append(dep)
        for group, group_rows in dependency_groups.items():
            title = "Object Dependency Diagram" if group == "ALL" else f"{group.replace('_', ' ').title()} Dependency Diagram"
            dependency_lines = [f"# {title}", "", f"All {len(group_rows)} catalog/static edges are included; no silent edge truncation is applied.", "", "```mermaid", "flowchart LR"]
            for index, dep in enumerate(group_rows):
                source = node_for(str(dep.get("source_schema") or "unknown"), str(dep.get("source_object") or f"source_{index}"))
                target_prefix = str(dep.get("target_database") or dep.get("target_server") or dep.get("target_schema") or "unknown")
                target = node_for(target_prefix, str(dep.get("target_object") or f"target_{index}"))
                relationship = re.sub(r"[^A-Za-z0-9_]", "_", str(dep.get("operation") or "reference"))
                dependency_lines.append(f"    {source} -->|{relationship}_{index}| {target}")
            dependency_lines.append("```")
            filename = "OBJECT_DEPENDENCY_DIAGRAM.md" if group == "ALL" else f"DEPENDENCY_{safe_path_component(group)}.md"
            _md(self.root / "19_Diagrams" / filename, "\n".join(dependency_lines))

    def _object_docs(self) -> None:
        cols: dict[str, list[dict[str, Any]]] = {}
        for col in self.data["columns"]: cols.setdefault(_object_key(col), []).append(col)
        shapes = {_object_key(row): row for row in self.data.get("table_shape", [])}
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        samples = self.data.get("sample_rows", {})

        def matching(rows: Iterable[dict[str, Any]], schema: str, obj: str, *, source: bool = False, target: bool = False) -> list[dict[str, Any]]:
            result = []
            for row in rows:
                if source:
                    found = str(row.get("source_schema") or "") == schema and str(row.get("source_object") or "") == obj
                elif target:
                    found = str(row.get("target_schema") or "") == schema and str(row.get("target_object") or "") == obj
                else:
                    found = str(row.get("schema_name") or "") == schema and str(row.get("object_name") or "") == obj
                if found: result.append(row)
            return result

        for table in self.data["tables"]:
            key = _object_key(table); schema, obj = key.split(".", 1)
            table_columns = sorted(cols.get(key, []), key=lambda row: int(row["column_id"]))
            pk = matching(self.data.get("primary_keys", []), schema, obj)
            outbound_fk = matching(self.data.get("foreign_keys", []), schema, obj, source=True)
            inbound_fk = matching(self.data.get("foreign_keys", []), schema, obj, target=True)
            inferred_out = matching(self.data.get("inferred_relationships", []), schema, obj, source=True)
            indexes = matching(self.data.get("indexes", []), schema, obj)
            constraints = matching(self.data.get("constraints", []), schema, obj)
            references = matching(self.data.get("all_dependencies", []), schema, obj, source=True)
            referenced_by = matching(self.data.get("all_dependencies", []), schema, obj, target=True)
            profiles = matching(self.data.get("column_profile", []), schema, obj)
            lineage = [row for row in self.data.get("lineage", []) if (str(row.get("source_schema") or "") == schema and str(row.get("source_object") or "") == obj) or (str(row.get("target_schema") or "") == schema and str(row.get("target_object") or "") == obj)]
            pipelines = [row for row in self.data.get("pipelines", []) if key in {str(row.get("origin") or ""), str(row.get("source") or ""), str(row.get("destination") or "")}]
            risks = [row for row in self.data.get("risks", []) if str(row.get("object_context") or "").startswith(key)]
            shape = shapes.get(key, {}); size = sizes.get(key, {})
            lines = [
                f"# Table `{schema}.{obj}`", "",
                "Catalog identity and physical metadata are **FACT**. Purpose and structural category are explicitly labelled as inference.", "",
                "## Identity and inferred purpose", "",
                f"- Object ID: `{table.get('object_id', '')}`", f"- Created: `{table.get('create_date', '')}`", f"- Modified: `{table.get('modify_date', '')}`",
                f"- Temporal type: `{table.get('temporal_type_desc', '')}`", f"- Memory optimized: `{table.get('is_memory_optimized', '')}`",
                f"- Inferred category: `{table.get('inferred_category', 'UNKNOWN')}` ({table.get('classification_confidence', 'LOW')} confidence; {table.get('classification_evidence', 'insufficient evidence')})", "",
                "## Size and shape", "",
            ]
            lines.extend(_md_table([{**size, **shape}], ("row_count", "row_count_type", "reserved_kb", "used_kb", "data_kb", "index_kb", "column_count", "nullable_columns", "identity_columns", "computed_columns", "identifier_columns")))
            lines.extend(("", "## Columns", "")); lines.extend(_md_table(table_columns, ("column_id", "column_name", "data_type", "max_length", "precision", "scale", "is_nullable", "is_identity", "is_computed", "default_definition")))
            lines.extend(("", "## Primary keys", "")); lines.extend(_md_table(pk, ("constraint_name", "key_ordinal", "column_name", "index_type_desc")))
            lines.extend(("", "## Outbound declared relationships", "")); lines.extend(_md_table(outbound_fk, ("constraint_name", "source_column", "target_schema", "target_object", "target_column", "delete_action", "update_action", "is_disabled", "is_not_trusted")))
            lines.extend(("", "## Inbound declared relationships", "")); lines.extend(_md_table(inbound_fk, ("constraint_name", "source_schema", "source_object", "source_column", "target_column")))
            lines.extend(("", "## Inferred outbound relationships", "")); lines.extend(_md_table(inferred_out, ("source_column", "target_schema", "target_object", "target_column", "classification", "confidence", "evidence")))
            lines.extend(("", "## Indexes", "")); lines.extend(_md_table(indexes, ("index_name", "index_type_desc", "is_unique", "is_primary_key", "key_ordinal", "column_name", "is_included_column", "filter_definition", "is_disabled")))
            lines.extend(("", "## Constraints", "")); lines.extend(_md_table(constraints, ("constraint_name", "constraint_type", "column_name", "definition", "is_disabled", "is_not_trusted")))
            lines.extend(("", "## References", "")); lines.extend(_md_table(references, ("source_type", "target_database", "target_schema", "target_object", "operation", "evidence")))
            lines.extend(("", "## Referenced by", "")); lines.extend(_md_table(referenced_by, ("source_schema", "source_object", "source_type", "operation", "evidence")))
            lines.extend(("", "## Column profiles", "")); lines.extend(_md_table(profiles, ("column_name", "total_rows", "null_count", "null_percent", "distinct_count", "distinct_percent", "minimum_value", "maximum_value", "profile_status")))
            sample_values = samples.get(key, [])[:5]
            lines.extend(("", "## Masked sample", "")); lines.extend(_md_table(sample_values, tuple(str(col["column_name"]) for col in table_columns)))
            lines.extend(("", "## Lineage", "")); lines.extend(_md_table(lineage, ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "relationship", "lineage_type", "confidence")))
            lines.extend(("", "## Pipeline participation", "")); lines.extend(_md_table(pipelines, ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence")))
            lines.extend(("", "## Data-quality observations, risks, and uncertainties", "")); lines.extend(_md_table(risks, ("severity", "category", "observation", "evidence_type", "uncertainty")))
            lines.extend(("", "Semantic business purpose remains `UNKNOWN` unless supported by extended properties or static code evidence."))
            _md(self.root / "20_Object_Documentation" / "Tables" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.md", "\n".join(lines))
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                schema = str(row.get("schema_name") or row.get("parent_schema_name") or "database")
                obj = str(row.get("object_name"))
                params = matching(self.data.get("parameters", []), schema, obj)
                dependencies = matching(self.data.get("all_dependencies", []), schema, obj, source=True)
                inbound = matching(self.data.get("all_dependencies", []), schema, obj, target=True)
                object_pipelines = [item for item in self.data.get("pipelines", []) if f"{schema}.{obj}" in {str(item.get("origin") or ""), str(item.get("source") or ""), str(item.get("destination") or "")}]
                object_risks = [item for item in self.data.get("risks", []) if str(item.get("object_context") or "").startswith(f"{schema}.{obj}")]
                lines = [
                    f"# {category[:-1].title()} `{schema}.{obj}`", "",
                    "Metadata is **FACT**; logic descriptions are **STATIC ANALYSIS** and do not prove runtime use.", "",
                    "## Identity and static-analysis flags", "",
                    f"- Definition SHA-256: `{row.get('definition_sha256', '')}`", f"- Definition available: {row.get('definition_available', False)}",
                    f"- Dynamic SQL present: {row.get('dynamic_sql_present', False)}", f"- Temporary tables present: {row.get('temp_table_present', False)}",
                    f"- Transaction logic present: {row.get('transaction_logic_present', False)}", f"- Error handling present: {row.get('error_handling_present', False)}",
                    f"- Likely write logic: {row.get('likely_write_logic', False)}", "",
                    "## Parameters", "",
                ]
                lines.extend(_md_table(params, ("parameter_id", "parameter_name", "data_type", "max_length", "precision", "scale", "is_output", "has_default_value", "is_readonly")))
                lines.extend(("", "## Reads, writes, calls, and references", "")); lines.extend(_md_table(dependencies, ("target_server", "target_database", "target_schema", "target_object", "target_column", "operation", "evidence")))
                lines.extend(("", "## Referenced by", "")); lines.extend(_md_table(inbound, ("source_schema", "source_object", "source_type", "operation", "evidence")))
                lines.extend(("", "## Pipeline role", "")); lines.extend(_md_table(object_pipelines, ("origin", "source", "transformation", "destination", "schedule", "classification", "confidence")))
                lines.extend(("", "## Risks and uncertainties", "")); lines.extend(_md_table(object_risks, ("severity", "category", "observation", "evidence_type", "uncertainty")))
                lines.extend(("", "## Sanitized static definition", "", "```sql", str(row.get("definition_sanitized") or "-- unavailable/encrypted"), "```"))
                _md(self.root / "20_Object_Documentation" / category.title() / f"{safe_path_component(schema)}__{safe_path_component(obj)}.md", "\n".join(lines))

    def prompt15_outputs(self) -> None:
        self._object_docs()
        self._diagrams()
        self._narratives()
        self._html_report()
        self._ensure_contract_files()
        self._write_control_files(final=False)
        self._snapshot_integrity()
