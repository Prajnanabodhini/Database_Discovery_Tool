"""Lineage-domain stages for the sequential discovery engine."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from ..programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from ..redaction import redact_text
from ..runtime import write_csv as _csv, write_markdown as _md
from .agent import SQL_AGENT_PIPELINE_HEADERS, SQL_AGENT_REFERENCE_HEADERS, analyze_agent_steps
from .static_sql import (
    definition_references as _definition_references,
    sanitized_external_server as _sanitized_external_server,
    static_column_references as _static_column_references,
    static_definition as _static_definition,
)


class LineageStagesMixin:
    """Programmable-object and lineage stages mixed into the orchestrator."""

    def _pipelines(self) -> None:
        rows: list[dict[str, Any]] = []
        object_flags = {(str(item.get("schema_name") or item.get("parent_schema_name") or ""), str(item.get("object_name") or "")): item for category in ("views", "procedures", "functions", "triggers") for item in self.data.get(category, [])}
        grouped_static: dict[tuple[str, str], dict[str, list[str]]] = {}
        for reference in self.data.get("static_references", []):
            source_key = (str(reference.get("source_schema") or ""), str(reference.get("source_object") or ""))
            target = ".".join(part for part in (str(reference.get("target_database") or ""), str(reference.get("target_schema") or ""), str(reference.get("target_object") or "")) if part)
            grouped_static.setdefault(source_key, {"READ": [], "WRITE": [], "CALL": []}).setdefault(str(reference.get("operation") or "REFERENCE"), []).append(target)
        for (schema, obj), operations in grouped_static.items():
            flags = object_flags.get((schema, obj), {})
            dynamic = bool(flags.get("dynamic_sql_present"))
            has_flow = bool(operations.get("READ") and operations.get("WRITE"))
            rows.append({
                "origin": f"{schema}.{obj}", "source": ", ".join(sorted(set(operations.get("READ", [])))) or "UNKNOWN",
                "transformation": f"STATIC_SQL_OBJECT; calls={', '.join(sorted(set(operations.get('CALL', [])))) or 'none'}",
                "destination": ", ".join(sorted(set(operations.get("WRITE", [])))) or "UNKNOWN", "schedule": "UNKNOWN",
                "read_write_evidence": "STATIC DEFINITION TOKEN ANALYSIS", "external_dependency": any("." in value and value.count(".") >= 2 for values in operations.values() for value in values),
                "classification": "DYNAMIC_SQL_OPAQUE" if dynamic else "LIKELY_PIPELINE" if has_flow else "CONFIRMED_DEPENDENCY",
                "confidence": "MEDIUM" if has_flow and not dynamic else "LOW" if dynamic else "MEDIUM", "evidence_class": "INFERENCE",
            })
        static_sources = set(grouped_static)
        for dep in self.data.get("dependencies", []):
            source_key = (str(dep.get("source_schema") or ""), str(dep.get("source_object") or ""))
            if source_key in static_sources:
                continue
            rows.append({"origin": f"{dep.get('source_schema')}.{dep.get('source_object')}", "source": f"{dep.get('target_schema')}.{dep.get('target_object')}", "transformation": dep.get("source_type"), "destination": "UNKNOWN", "schedule": "UNKNOWN", "read_write_evidence": "CATALOG REFERENCE; DIRECTION UNKNOWN", "external_dependency": bool(dep.get("target_server") or dep.get("target_database")), "classification": "HISTORICAL_OR_UNKNOWN", "confidence": "MEDIUM" if dep.get("referenced_id") else "LOW", "evidence_class": "FACT" if dep.get("referenced_id") else "INFERENCE"})
        rows.extend(dict(edge) for edge in self.data.get("sql_agent_pipeline_edges", []))
        self.data["pipelines"] = rows
        _csv(self.artifact("PIPELINE_CATALOGUE.csv"), ("origin", "source", "transformation", "destination", "schedule", "read_write_evidence", "external_dependency", "classification", "confidence", "evidence_class", "job_name", "step_id", "step_name", "subsystem", "operation", "reference_kind", "dynamic_sql_opaque"), rows)

    def prompt12_external(self) -> None:
        rows = []
        for dep in self.data.get("all_dependencies", self.data.get("dependencies", [])):
            if dep.get("target_server") or dep.get("target_database"):
                rows.append({**dep, "reference_kind": "FOUR_PART" if dep.get("target_server") else "THREE_PART", "queried_external_system": False})
        for synonym in self.data.get("synonyms", []):
            base = str(synonym.get("base_object_name") or "")
            if base.count(".") >= 2:
                parts = [part.strip("[]") for part in base.split(".")]
                if len(parts) >= 4:
                    parts[0] = _sanitized_external_server(parts[0])
                safe_base = ".".join(parts)
                rows.append({
                    "source_server": "[SANITIZED]", "source_database": self.database,
                    "source_schema": synonym.get("schema_name"), "source_object": synonym.get("object_name"),
                    "source_type": "SYNONYM", "target_server": "", "target_database": "",
                    "target_schema": "", "target_object": safe_base, "reference_kind": "SYNONYM_EXTERNAL",
                    "queried_external_system": False,
                })
        for category in ("views", "procedures", "functions", "triggers"):
            for obj in self.data.get(category, []):
                definition = str(obj.get("definition_sanitized") or "")
                for construct in ("OPENQUERY", "OPENROWSET", "OPENDATASOURCE"):
                    if re.search(rf"\b{construct}\s*\(", definition, re.I):
                        rows.append({
                            "source_server": "[SANITIZED]", "source_database": self.database,
                            "source_schema": obj.get("schema_name") or obj.get("parent_schema_name"),
                            "source_object": obj.get("object_name"), "source_type": category[:-1].upper(),
                            "target_server": "[STATIC_TEXT_REDACTED]", "target_database": "", "target_schema": "", "target_object": "",
                            "reference_kind": construct, "queried_external_system": False,
                        })
        linked_servers = self.fetch_dynamic(
            "SELECT name, product, provider, is_linked, is_data_access_enabled, is_rpc_out_enabled FROM sys.servers WHERE server_id > 0 ORDER BY name",
            prompt="12", stage="linked_server_metadata", schema="sys", obj="servers", query_name="linked_servers",
        )
        safe_linked_servers = []
        for item in linked_servers:
            digest = hashlib.sha256(str(item.get("name") or "").encode("utf-8", errors="replace")).hexdigest()[:12]
            safe_linked_servers.append({**item, "name": f"[EXTERNAL_SERVER:{digest}]"})
        self.data["linked_servers"] = safe_linked_servers
        _csv(self.artifact("LINKED_SERVER_CATALOGUE.csv"), tuple(safe_linked_servers[0]) if safe_linked_servers else ("name", "product", "provider", "is_linked", "is_data_access_enabled", "is_rpc_out_enabled"), safe_linked_servers)
        self.data["external"] = rows
        _csv(self.artifact("CROSS_DATABASE_SERVER_REFERENCES.csv"), tuple(rows[0]) if rows else ("source_server", "source_database", "source_schema", "source_object", "source_type", "target_server", "target_database", "target_schema", "target_object", "reference_kind", "queried_external_system"), rows)

    def prompt11_lineage(self) -> None:
        deps = [dict(row) for row in self.data.get("dependencies", [])]
        for row in deps:
            if row.get("target_server"):
                row["target_server"] = _sanitized_external_server(row["target_server"])
        existing = {
            (str(row.get("source_schema") or "").casefold(), str(row.get("source_object") or "").casefold(), str(row.get("target_database") or "").casefold(), str(row.get("target_schema") or "").casefold(), str(row.get("target_object") or "").casefold())
            for row in deps
        }
        for reference in self.data.get("static_references", []):
            reference = dict(reference)
            if reference.get("target_server"):
                reference["target_server"] = _sanitized_external_server(reference["target_server"])
            key = (str(reference.get("source_schema") or "").casefold(), str(reference.get("source_object") or "").casefold(), str(reference.get("target_database") or "").casefold(), str(reference.get("target_schema") or "").casefold(), str(reference.get("target_object") or "").casefold())
            if key in existing:
                continue
            deps.append({
                **reference, "source_column_id": "", "target_column": "", "referenced_id": "",
                "is_schema_bound_reference": "", "is_caller_dependent": "", "is_ambiguous": "",
            })
            existing.add(key)
        self.data["all_dependencies"] = deps
        _csv(self.artifact("OBJECT_DEPENDENCIES.csv"), tuple(deps[0]) if deps else self._programmable_headers("dependencies"), deps)
        source_columns = {(int(col["object_id"]), int(col["column_id"])): col["column_name"] for col in self.data.get("columns", [])}
        object_ids = {(str(row.get("source_schema")), str(row.get("source_object"))): next((int(obj["object_id"]) for group in (self.data.get("views", []), self.data.get("procedures", []), self.data.get("functions", [])) for obj in group if str(obj.get("schema_name")) == str(row.get("source_schema")) and str(obj.get("object_name")) == str(row.get("source_object"))), 0) for row in deps}
        lineage = []
        definitions = {(str(row.get("schema_name") or row.get("parent_schema_name") or ""), str(row.get("object_name") or "")): str(row.get("definition_sanitized") or "") for category in ("views", "procedures", "functions", "triggers") for row in self.data.get(category, [])}
        for row in deps:
            object_id = object_ids.get((str(row.get("source_schema")), str(row.get("source_object"))), 0)
            source_column = source_columns.get((object_id, int(row.get("source_column_id") or 0)), "")
            definition = definitions.get((str(row.get("source_schema") or ""), str(row.get("source_object") or "")), "")
            if source_column and row.get("target_column"):
                lineage_type = "DIRECT"
            elif row.get("target_column") and re.search(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", definition, re.I):
                lineage_type = "AGGREGATED"
            elif row.get("target_column") and re.search(r"\bCASE\b", definition, re.I):
                lineage_type = "CONDITIONAL"
            elif row.get("target_column") and re.search(r"[+*/-]", definition):
                lineage_type = "DERIVED"
            else:
                lineage_type = "UNKNOWN"
            lineage.append({
                **row, "source_column": source_column, "relationship": row.get("operation") or "REFERENCE", "lineage_type": lineage_type,
                "evidence": row.get("evidence") or "sys.sql_expression_dependencies", "confidence": "HIGH" if row.get("referenced_id") else "MEDIUM" if row.get("target_schema") else "LOW",
                "evidence_class": row.get("evidence_class") or ("FACT" if row.get("referenced_id") else "INFERENCE"),
            })
        known_columns: dict[tuple[str, str], set[str]] = {}
        for column in self.data.get("columns", []):
            if column.get("object_type") == "USER_TABLE":
                known_columns.setdefault((str(column["schema_name"]), str(column["object_name"])), set()).add(str(column["column_name"]).casefold())
        static_seen: set[tuple[str, str, str, str, str, str]] = set()
        for category in ("views", "procedures", "functions", "triggers"):
            for obj in self.data.get(category, []):
                source_schema = str(obj.get("schema_name") or obj.get("parent_schema_name") or "")
                source_object = str(obj.get("object_name") or "")
                for reference in _static_column_references(obj, known_columns):
                    key = (source_schema.casefold(), source_object.casefold(), reference["target_schema"].casefold(), reference["target_object"].casefold(), reference["target_column"].casefold(), reference["lineage_type"])
                    if key in static_seen:
                        continue
                    static_seen.add(key)
                    lineage.append({
                        "source_server": "[SANITIZED]", "source_database": self.database,
                        "source_schema": source_schema, "source_object": source_object, "source_type": category[:-1].upper(),
                        "source_column": "EXPRESSION_OUTPUT_UNKNOWN", "target_server": "", "target_database": self.database,
                        "target_schema": reference["target_schema"], "target_object": reference["target_object"], "target_column": reference["target_column"],
                        "relationship": "COLUMN_REFERENCE", "lineage_type": reference["lineage_type"],
                        "evidence": reference["evidence"], "confidence": "MEDIUM", "evidence_class": "INFERENCE",
                    })
        for reference in self.data.get("sql_agent_step_references", []):
            lineage.append({
                "source_server": "[SANITIZED]", "source_database": reference.get("source_database") or self.database,
                "source_schema": "SQL_AGENT", "source_object": reference.get("job_name"),
                "source_type": "SQL_AGENT_STEP",
                "source_column": f"step {reference.get('step_id', '')}: {reference.get('step_name', '')}".strip(),
                "target_server": reference.get("target_server", ""),
                "target_database": reference.get("target_database", ""),
                "target_schema": reference.get("target_schema", ""),
                "target_object": reference.get("target_object", ""), "target_column": "",
                "relationship": reference.get("operation") or "OPAQUE", "lineage_type": "UNKNOWN",
                "evidence": reference.get("evidence", ""), "confidence": reference.get("confidence", "LOW"),
                "evidence_class": reference.get("evidence_class", "INFERENCE"),
                "reference_kind": reference.get("reference_kind", ""),
                "dynamic_sql_opaque": reference.get("dynamic_sql_opaque", False),
            })
        self.data["lineage"] = lineage
        lineage_headers = tuple(dict.fromkeys(key for row in lineage for key in row)) if lineage else ("source_database", "source_schema", "source_object", "target_database", "target_schema", "target_object", "relationship", "lineage_type", "evidence", "confidence", "evidence_class")
        _csv(self.artifact("LINEAGE_EDGES.csv"), lineage_headers, lineage)
        view_deps = [row for row in deps if row.get("source_type") == "VIEW"]
        sp_deps = [row for row in deps if row.get("source_type") in {"SQL_STORED_PROCEDURE", "CLR_STORED_PROCEDURE"}]
        _csv(self.artifact("VIEW_DEPENDENCIES.csv"), tuple(view_deps[0]) if view_deps else self._programmable_headers("dependencies"), view_deps)
        _csv(self.artifact("STORED_PROCEDURE_DEPENDENCIES.csv"), tuple(sp_deps[0]) if sp_deps else self._programmable_headers("dependencies"), sp_deps)
        lineage_counts = {kind: sum(row.get("lineage_type") == kind for row in lineage) for kind in ("DIRECT", "DERIVED", "AGGREGATED", "CONDITIONAL", "UNKNOWN")}
        _md(self.artifact("LINEAGE_SUMMARY.md"), "# Lineage Summary\n\n" + "\n".join((
            f"- Object dependency edges: {len(deps)}", f"- Lineage edges: {len(lineage)}",
            f"- SQL Agent step reference edges: {len(self.data.get('sql_agent_step_references', []))}",
            *(f"- {kind.title()} classifications: {count}" for kind, count in lineage_counts.items()),
            "- `UNKNOWN` is retained where catalog/static evidence cannot safely resolve column transformation semantics.",
            "- Dynamic SQL may be opaque and is reported separately.",
        )))
        degree: dict[str, dict[str, int]] = {}
        for row in deps:
            source = f"{row.get('source_schema')}.{row.get('source_object')}"
            target = f"{row.get('target_schema')}.{row.get('target_object')}"
            degree.setdefault(source, {"inbound": 0, "outbound": 0})["outbound"] += 1
            degree.setdefault(target, {"inbound": 0, "outbound": 0})["inbound"] += 1
        impact = [{"object_name": key, **value, "total_edges": value["inbound"] + value["outbound"], "interpretation": "STRUCTURAL_CENTRALITY_NOT_BUSINESS_CRITICALITY"} for key, value in degree.items()]
        impact.sort(key=lambda row: int(row["total_edges"]), reverse=True)
        _csv(self.artifact("HIGH_IMPACT_OBJECTS.csv"), tuple(impact[0]) if impact else ("object_name", "inbound", "outbound", "total_edges", "interpretation"), impact)

    @staticmethod
    @staticmethod
    def _programmable_headers(name: str) -> tuple[str, ...]:
        common = ("server_name", "database_name", "schema_name", "object_name", "object_id")
        if name == "dependencies":
            return ("source_server", "source_database", "source_schema", "source_object", "source_type", "source_column_id", "target_server", "target_database", "target_schema", "target_object", "target_column", "is_schema_bound_reference", "is_caller_dependent", "is_ambiguous", "referenced_id")
        if name == "parameters":
            return common + ("object_type", "parameter_id", "parameter_name", "data_type", "max_length", "precision", "scale", "is_output", "has_default_value", "default_value", "is_readonly")
        return common

    def prompt05_programmable(self) -> None:
        mapping = {
            "views": "VIEW_CATALOGUE.csv", "procedures": "STORED_PROCEDURE_CATALOGUE.csv",
            "functions": "FUNCTION_CATALOGUE.csv", "triggers": "TRIGGER_CATALOGUE.csv",
            "synonyms": "SYNONYM_CATALOGUE.csv", "sequences": "SEQUENCE_CATALOGUE.csv",
            "parameters": "PARAMETER_CATALOGUE.csv", "dependencies": "OBJECT_DEPENDENCIES.csv",
        }
        for query in PROGRAMMABLE_QUERIES:
            rows = self.fetch(query, prompt="05", optional=True)
            if query.name in {"views", "procedures", "functions", "triggers"}:
                rows = [_static_definition(dict(row)) for row in rows]
                for row in rows:
                    row["definition_sanitized"] = redact_text(row.get("definition_sanitized", ""), sensitive_values=self.sensitive_values)
            self.data[query.name] = rows
            headers = list(rows[0]) if rows else self._programmable_headers(query.name)
            _csv(self.artifact(mapping[query.name]), headers, rows)
        static_references: list[dict[str, Any]] = []
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                source_schema = str(row.get("schema_name") or row.get("parent_schema_name") or "")
                for reference in _definition_references(row):
                    static_references.append({
                        "source_server": "[SANITIZED]", "source_database": self.database,
                        "source_schema": source_schema, "source_object": row.get("object_name"),
                        "source_type": category[:-1].upper(), **reference,
                    })
        self.data["static_references"] = static_references
        raw_jobs = self.fetch(SQL_AGENT_QUERY, prompt="05", optional=True) if self.settings.discover_sql_agent_jobs else []
        jobs, agent_references, agent_pipeline_edges = analyze_agent_steps(
            raw_jobs,
            sensitive_values=self.sensitive_values,
        )
        self.data["sql_agent_jobs"] = jobs
        self.data["sql_agent_step_references"] = agent_references
        self.data["sql_agent_pipeline_edges"] = agent_pipeline_edges
        job_headers = list(jobs[0]) if jobs else (
            "server_name", "job_name", "job_enabled", "description", "step_id", "step_name",
            "subsystem", "command_sha256", "database_name", "schedule_name",
            "command_text_sanitized", "invocation_hint", "command_classification", "dynamic_sql_opaque",
        )
        _csv(self.artifact("SQL_AGENT_JOB_CATALOGUE.csv"), job_headers, jobs)
        _csv(self.artifact("SQL_AGENT_STEP_REFERENCES.csv"), SQL_AGENT_REFERENCE_HEADERS, agent_references)
        _csv(self.artifact("SQL_AGENT_PIPELINE_EDGES.csv"), SQL_AGENT_PIPELINE_HEADERS, agent_pipeline_edges)
