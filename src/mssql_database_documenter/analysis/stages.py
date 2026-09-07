"""Analysis-domain stages for the sequential discovery engine."""

from __future__ import annotations

import re

from ..contracts import EVIDENCE_CLASSES
from ..runtime import object_key as _object_key, write_csv as _csv, write_markdown as _md


class AnalysisStagesMixin:
    """Classification, duplicate, quality, and risk stages."""

    def prompt14_quality(self) -> None:
        table_keys = {_object_key(row) for row in self.data["tables"]}
        pk_keys = {_object_key(row) for row in self.data.get("primary_keys", [])}
        missing = sorted(table_keys - pk_keys)
        missing_rows = [{"database_name": self.database, "schema_name": key.split(".", 1)[0], "object_name": key.split(".", 1)[1], "observation": "NO_DECLARED_PRIMARY_KEY", "evidence": "FACT"} for key in missing]
        _csv(self.artifact("TABLES_WITHOUT_PRIMARY_KEY.csv"), ("database_name", "schema_name", "object_name", "observation", "evidence"), missing_rows)
        risks: list[dict[str, Any]] = []
        def add(severity: str, category: str, context: str, observation: str, evidence: str, uncertainty: str) -> None:
            if evidence not in EVIDENCE_CLASSES:
                raise ValueError(f"Invalid evidence class: {evidence}")
            risks.append({"severity": severity, "category": category, "object_context": context, "observation": observation, "evidence_type": evidence, "uncertainty": uncertainty})
        for row in missing_rows: add("Medium", "Structure", f"{row['schema_name']}.{row['object_name']}", "Table has no declared primary key", "FACT", "Business intent unknown; another unique key may exist")
        if not self.data.get("foreign_keys"): risks.append({"severity": "High", "category": "Relationships", "object_context": self.database, "observation": "No declared foreign keys are visible", "evidence_type": "FACT", "uncertainty": "Integrity may be enforced in application code or permissions may limit visibility"})
        for row in self.data.get("column_profile", []):
            if row.get("profile_status") == "PROFILED" and str(row.get("total_rows")) not in {"", "0"}:
                context = f"{row['schema_name']}.{row['object_name']}.{row['column_name']}"
                if int(row.get("non_null_count") or 0) == 0: add("Low", "Data Quality", context, "Column is all null", "DATA_VALIDATION", "Current snapshot only")
                elif str(row.get("distinct_count")) not in {"", "None"} and int(row.get("distinct_count") or 0) == 1: add("Informational", "Data Quality", context, "Column is constant", "DATA_VALIDATION", "Current snapshot only")
                if int(row.get("empty_string_count") or 0) > 0: add("Low", "Data Quality", context, f"Contains {row['empty_string_count']} empty strings", "DATA_VALIDATION", "Empty strings may be valid business values")
                whitespace = int(row.get("whitespace_string_count") or 0)
                empty = int(row.get("empty_string_count") or 0)
                if whitespace > empty: add("Low", "Data Quality", context, f"Contains {whitespace - empty} whitespace-only non-empty strings", "DATA_VALIDATION", "Current snapshot only")
                if int(row.get("negative_count") or 0) > 0: add("Informational", "Numeric Range", context, f"Contains {row['negative_count']} negative values", "DATA_VALIDATION", "Negative values may be valid; semantic range is unknown")
            elif str(row.get("profile_status") or "").startswith("SKIPPED"):
                add("Informational", "Coverage", f"{row['schema_name']}.{row['object_name']}.{row['column_name']}", f"Profiling {row['profile_status']}", "FACT", "No data-level conclusion is possible")
        for row in self.data.get("orphan_analysis", []):
            if int(row.get("orphan_rows") or 0) > 0:
                add("Medium" if row.get("classification") == "DECLARED_FK" else "Low", "Relationships", f"{row['source_schema']}.{row['source_object']}.{row['source_column']}", f"Observed {row['orphan_rows']} unmatched non-null references", "DATA_VALIDATION", "Inferred relationships may be semantically unrelated")
        for row in self.data.get("foreign_keys", []):
            if row.get("is_disabled") or row.get("is_not_trusted"):
                add("High" if row.get("is_disabled") else "Medium", "Constraint", f"{row['source_schema']}.{row['source_object']}.{row['constraint_name']}", "Foreign key is disabled or untrusted", "FACT", "Current catalog state")
        for row in self.data.get("constraints", []):
            if row.get("is_disabled") or row.get("is_not_trusted"):
                add("Medium", "Constraint", f"{row['schema_name']}.{row['object_name']}.{row['constraint_name']}", "Constraint is disabled or untrusted", "FACT", "Current catalog state")
        for category in ("views", "procedures", "functions", "triggers"):
            for row in self.data.get(category, []):
                context = f"{row.get('schema_name') or row.get('parent_schema_name')}.{row.get('object_name')}"
                if not row.get("definition_available"): add("Medium", "Static Analysis", context, "Definition unavailable or encrypted", "FACT", "Dependencies and logic may be incomplete")
                if row.get("dynamic_sql_present"): add("Medium", "Dynamic SQL", context, "Dynamic SQL is present", "INFERENCE", "Runtime targets may remain opaque")
        for row in self.data.get("external", []):
            add("Medium", "External Dependency", f"{row.get('source_schema')}.{row.get('source_object')}", f"External reference detected: {row.get('reference_kind')}", "INFERENCE", "External system was not queried")
        for error in self.errors:
            add("Medium", "Access or Discovery Limitation", f"{error.get('schema_name')}.{error.get('object_name')}".strip("."), str(error.get("impact") or "Evidence unavailable"), "FACT", str(error.get("sanitized_message") or ""))
        self.data["risks"] = risks
        _csv(self.artifact("RISK_AND_UNCERTAINTY_REGISTER.csv"), tuple(risks[0]) if risks else ("severity", "category", "object_context", "observation", "evidence_type", "uncertainty"), risks)
        _md(self.artifact("DATA_QUALITY_SUMMARY.md"), f"# Data Quality Summary\n\n- Tables without declared primary keys: {len(missing)}\n- Declared foreign-key rows: {len(self.data.get('foreign_keys', []))}\n- Profile observations recorded: {sum(1 for row in self.data.get('column_profile', []) if row.get('profile_status') == 'PROFILED')}\n- Orphan analyses with unmatched rows: {sum(int(row.get('orphan_rows') or 0) > 0 for row in self.data.get('orphan_analysis', []))}\n- Disabled/untrusted FK rows: {sum(bool(row.get('is_disabled') or row.get('is_not_trusted')) for row in self.data.get('foreign_keys', []))}\n- Dynamic-SQL objects: {sum(bool(row.get('dynamic_sql_present')) for category in ('views', 'procedures', 'functions', 'triggers') for row in self.data.get(category, []))}\n- Risk-register entries: {len(risks)}\n\nSeverity is cautious; semantic meaning remains unknown unless explicitly documented. Duplicate-key and semantic range conclusions require declared/candidate key evidence and are not guessed from names alone.")

    def prompt13_classification(self) -> None:
        shapes = {_object_key(row): row for row in self.data.get("table_shape", [])}
        pk_counts: dict[str, int] = {}
        fk_out_counts: dict[str, int] = {}
        fk_in_counts: dict[str, int] = {}
        index_counts: dict[str, set[str]] = {}
        constraint_counts: dict[str, set[str]] = {}
        for row in self.data.get("primary_keys", []): pk_counts[_object_key(row)] = pk_counts.get(_object_key(row), 0) + 1
        for row in self.data.get("foreign_keys", []):
            source = f"{row['source_schema']}.{row['source_object']}"; target = f"{row['target_schema']}.{row['target_object']}"
            fk_out_counts[source] = fk_out_counts.get(source, 0) + 1; fk_in_counts[target] = fk_in_counts.get(target, 0) + 1
        for row in self.data.get("indexes", []): index_counts.setdefault(_object_key(row), set()).add(str(row.get("index_name") or ""))
        for row in self.data.get("constraints", []): constraint_counts.setdefault(_object_key(row), set()).add(str(row.get("constraint_name") or ""))
        buckets: dict[str, list[dict[str, Any]]] = {"MASTER": [], "LOOKUP": [], "TRANSACTION": [], "BRIDGE": [], "HISTORY": [], "AUDIT": [], "STAGING": [], "ARCHIVE": [], "CONFIGURATION": []}
        classified = []
        for table in self.data["tables"]:
            key = _object_key(table)
            name = str(table["object_name"]).lower()
            shape = shapes.get(key, {})
            row_count = int(shape.get("estimated_rows") or 0)
            column_count = int(shape.get("column_count") or 0)
            confidence = "LOW"; evidence = "structural inference only"
            if re.search(r"audit|log", name): category = "AUDIT"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"history", name): category = "HISTORY"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"archive|backup|old", name): category = "ARCHIVE"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"stage|staging|import|temp", name): category = "STAGING"; confidence = "MEDIUM"; evidence = "name pattern"
            elif re.search(r"config|setting|option", name): category = "CONFIGURATION"; confidence = "MEDIUM"; evidence = "name pattern"
            elif fk_out_counts.get(key, 0) >= 2 and column_count <= 16: category = "BRIDGE"; confidence = "MEDIUM"; evidence = "multiple outbound FKs and narrow shape"
            elif re.search(r"map|bridge|link|detail", name) and column_count <= 16: category = "BRIDGE"; evidence = "name and narrow shape"
            elif re.search(r"lookup|type|status|master", name) or (row_count <= 100 and column_count <= 12): category = "LOOKUP"; evidence = "name or small narrow shape"
            elif re.search(r"transaction|invoice|payment|receipt|order|entry", name): category = "TRANSACTION"; confidence = "MEDIUM"; evidence = "name pattern"
            elif fk_in_counts.get(key, 0) >= 2: category = "MASTER"; evidence = "multiple inbound FK references"
            else: category = "UNKNOWN"; evidence = "insufficient structural evidence"
            item = {"server_name": "[SANITIZED]", "database_name": self.database, "schema_name": table["schema_name"], "object_name": table["object_name"], "inferred_category": category, "confidence": confidence, "evidence": evidence, "evidence_class": "UNKNOWN" if category == "UNKNOWN" else "INFERENCE"}
            if category in buckets: buckets[category].append(item)
            classified.append(item)
            table.update({
                "estimated_rows": row_count, "column_count": column_count,
                "primary_key_column_count": pk_counts.get(key, 0), "foreign_key_outbound_count": fk_out_counts.get(key, 0),
                "foreign_key_inbound_count": fk_in_counts.get(key, 0), "index_count": len(index_counts.get(key, set())),
                "constraint_count": len(constraint_counts.get(key, set())), "inferred_category": category,
                "classification_confidence": confidence, "classification_evidence": evidence,
            })
        names = {"MASTER": "POSSIBLE_MASTER_TABLES.csv", "LOOKUP": "POSSIBLE_LOOKUP_TABLES.csv", "TRANSACTION": "POSSIBLE_TRANSACTION_TABLES.csv", "BRIDGE": "POSSIBLE_BRIDGE_TABLES.csv", "HISTORY": "POSSIBLE_HISTORY_AUDIT_TABLES.csv"}
        headers = ("server_name", "database_name", "schema_name", "object_name", "inferred_category", "confidence", "evidence", "evidence_class")
        for category, filename in names.items():
            selected = buckets[category]
            if category == "HISTORY": selected = selected + buckets["AUDIT"]
            _csv(self.artifact(filename), headers, selected)
        other = buckets["STAGING"] + buckets["ARCHIVE"] + buckets["CONFIGURATION"]
        _csv(self.artifact("OTHER_STRUCTURAL_CLASSIFICATIONS.csv"), headers, other)
        if self.data.get("tables"):
            _csv(self.artifact("TABLE_CATALOGUE.csv"), tuple(self.data["tables"][0]), self.data["tables"])
        column_sets: dict[str, set[str]] = {}
        for col in self.data["columns"]:
            if col.get("object_type") == "USER_TABLE": column_sets.setdefault(_object_key(col), set()).add(str(col["column_name"]).casefold())
        duplicates = []
        keys = sorted(column_sets)
        for index, left in enumerate(keys):
            for right in keys[index + 1:]:
                union = column_sets[left] | column_sets[right]
                score = len(column_sets[left] & column_sets[right]) / len(union) if union else 0
                if score >= 0.8: duplicates.append((left, right, score))
        lines = ["# Possible Duplicate or Legacy Structures", "", "All entries are inference, not fact.", ""]
        lines.extend(f"- `{left}` ↔ `{right}`: column-name Jaccard similarity {score:.2f}" for left, right, score in duplicates)
        if not duplicates: lines.append("No pairs crossed the 0.80 structural-similarity threshold.")
        _md(self.artifact("POSSIBLE_DUPLICATE_OR_LEGACY_STRUCTURES.md"), "\n".join(lines))
