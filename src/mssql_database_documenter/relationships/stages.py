"""Relationship inference, cardinality, and orphan-validation stage ownership."""

from __future__ import annotations

import re
from typing import Any

from ..profiling import within_safety_threshold as _within_safety_threshold
from ..runtime import object_key as _object_key, quote_identifier as _qid, write_csv as _csv
from .inference import normalized_identifier as _normalized_identifier


class RelationshipStagesMixin:
    """Relationship domain stage mixed into the sequential orchestrator."""

    def prompt10_relationships(self) -> None:
        columns = self.data["columns"]
        column_lookup = {(_object_key(c), str(c["column_name"])): c for c in columns}
        declared = self.data.get("foreign_keys", [])
        declared_sources = {(str(row["source_schema"]), str(row["source_object"]), str(row["source_column"])) for row in declared}

        unique_targets: list[dict[str, Any]] = []
        pk_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in self.data.get("primary_keys", []):
            pk_groups.setdefault((str(row["schema_name"]), str(row["object_name"]), str(row["constraint_name"])), []).append(row)
        for group in pk_groups.values():
            if len(group) == 1:
                unique_targets.append({**group[0], "unique_evidence": "PRIMARY_KEY"})
        index_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in self.data.get("indexes", []):
            if row.get("is_unique") and int(row.get("key_ordinal") or 0) > 0:
                index_groups.setdefault((str(row["schema_name"]), str(row["object_name"]), str(row.get("index_name") or "")), []).append(row)
        for group in index_groups.values():
            if len(group) == 1:
                item = group[0]
                unique_targets.append({"schema_name": item["schema_name"], "object_name": item["object_name"], "column_name": item["column_name"], "unique_evidence": "UNIQUE_INDEX"})

        inferred: list[dict[str, Any]] = []
        for col in columns:
            source_identity = (str(col["schema_name"]), str(col["object_name"]), str(col["column_name"]))
            if col.get("object_type") != "USER_TABLE" or source_identity in declared_sources:
                continue
            source_name = str(col["column_name"])
            if not re.search(r"(^id$|id$|_id$|code$|no$)", source_name, re.I):
                continue
            scored: list[tuple[int, dict[str, Any], str]] = []
            for target in unique_targets:
                if str(target["schema_name"]) == source_identity[0] and str(target["object_name"]) == source_identity[1]:
                    continue
                target_column = column_lookup.get((f"{target['schema_name']}.{target['object_name']}", str(target["column_name"])))
                if not target_column or str(target_column.get("data_type") or "").casefold() != str(col.get("data_type") or "").casefold():
                    continue
                source_norm = _normalized_identifier(source_name)
                target_col_norm = _normalized_identifier(str(target["column_name"]))
                target_table_norm = _normalized_identifier(str(target["object_name"]))
                score = 2
                evidence = ["compatible type", str(target["unique_evidence"]).lower()]
                if source_norm == target_col_norm:
                    score += 4; evidence.append("matching column name")
                if source_norm in {target_table_norm + "id", target_table_norm.rstrip("s") + "id"}:
                    score += 5; evidence.append("table-name identifier pattern")
                elif target_table_norm and target_table_norm in source_norm:
                    score += 3; evidence.append("table-name overlap")
                if score >= 6:
                    scored.append((score, target, "; ".join(evidence)))
            for score, target, evidence in sorted(scored, key=lambda item: item[0], reverse=True)[:3]:
                inferred.append({
                    "server_name": "[SANITIZED]", "database_name": self.database,
                    "source_schema": source_identity[0], "source_object": source_identity[1], "source_column": source_name,
                    "target_schema": target["schema_name"], "target_object": target["object_name"], "target_column": target["column_name"],
                    "classification": "SCHEMA_INFERRED", "confidence": "HIGH" if score >= 10 else "MEDIUM" if score >= 8 else "LOW",
                    "evidence": evidence, "evidence_class": "INFERENCE", "inference_score": score,
                })

        self.data["inferred_relationships"] = inferred
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        cardinality: list[dict[str, Any]] = []
        orphans: list[dict[str, Any]] = []
        relationship_rows: list[dict[str, Any]] = []
        fk_counts: dict[tuple[str, str, str], int] = {}
        for fk in declared:
            key = (str(fk["source_schema"]), str(fk["source_object"]), str(fk["constraint_name"]))
            fk_counts[key] = fk_counts.get(key, 0) + 1
            relationship_rows.append({**fk, "classification": "DECLARED_FK", "confidence": "HIGH", "evidence": "sys.foreign_keys", "evidence_class": "FACT"})
        relationship_rows.extend(inferred)

        for row in relationship_rows:
            source_key = f"{row['source_schema']}.{row['source_object']}"; target_key = f"{row['target_schema']}.{row['target_object']}"
            composite = row.get("classification") == "DECLARED_FK" and fk_counts.get((str(row["source_schema"]), str(row["source_object"]), str(row.get("constraint_name") or "")), 0) > 1
            validation: dict[str, Any] | None = None
            if (
                not composite
                and _within_safety_threshold(sizes, source_key, self.mode_policy.relationship_validation_threshold)
                and _within_safety_threshold(sizes, target_key, self.mode_policy.relationship_validation_threshold)
            ):
                scol = _qid(str(row["source_column"])); tcol = _qid(str(row["target_column"]))
                sql = (
                    f"SELECT COUNT_BIG(*) AS source_rows, SUM(CASE WHEN s.{scol} IS NULL THEN 1 ELSE 0 END) AS null_source_values, "
                    f"COUNT_BIG(DISTINCT s.{scol}) AS source_distinct_values, "
                    f"SUM(CASE WHEN s.{scol} IS NOT NULL AND t.{tcol} IS NULL THEN 1 ELSE 0 END) AS orphan_rows "
                    f"FROM {_qid(str(row['source_schema']))}.{_qid(str(row['source_object']))} AS s "
                    f"LEFT JOIN {_qid(str(row['target_schema']))}.{_qid(str(row['target_object']))} AS t ON t.{tcol} = s.{scol}"
                )
                result = self.fetch_dynamic(sql, prompt="10", stage="relationship_validation", schema=str(row["source_schema"]), obj=str(row["source_object"]), query_name=str(row["source_column"]))
                validation = result[0] if result else None
            if validation:
                source_rows = int(validation.get("source_rows") or 0); nulls = int(validation.get("null_source_values") or 0)
                orphan_count = int(validation.get("orphan_rows") or 0); distincts = int(validation.get("source_distinct_values") or 0); nonnull = source_rows - nulls
                if row.get("classification") != "DECLARED_FK":
                    row["classification"] = "DATA_VALIDATED"; row["confidence"] = "HIGH" if orphan_count == 0 else "MEDIUM"
                    row["evidence"] = str(row.get("evidence") or "") + "; value-domain join validation"
                    row["evidence_class"] = "DATA_VALIDATION"
                likely = "1:1" if nonnull == distincts else "N:1"
                cardinality.append({**row, "likely_cardinality": likely, "optionality": "OPTIONAL" if nulls else "REQUIRED_IN_CURRENT_DATA", "validation_status": "DATA_VALIDATED"})
                orphans.append({**row, "source_rows": source_rows, "null_source_values": nulls, "orphan_rows": orphan_count, "matched_rows": nonnull - orphan_count, "orphan_percent": round(orphan_count * 100.0 / nonnull, 4) if nonnull else 0.0, "analysis_status": "DATA_VALIDATED"})
            else:
                reason = "COMPOSITE_RELATIONSHIP_NOT_SCANNED_PER_COLUMN" if composite else "SKIPPED_FOR_SAFETY_OR_ACCESS"
                cardinality.append({**row, "likely_cardinality": "N:1" if not composite else "UNKNOWN", "optionality": "UNKNOWN", "validation_status": reason})
                orphans.append({**row, "source_rows": "", "null_source_values": "", "orphan_rows": "", "matched_rows": "", "orphan_percent": "", "analysis_status": reason})

        by_source: dict[str, set[str]] = {}
        for fk in declared:
            by_source.setdefault(f"{fk['source_schema']}.{fk['source_object']}", set()).add(f"{fk['target_schema']}.{fk['target_object']}")
        for bridge, targets in sorted(by_source.items()):
            if len(targets) >= 2:
                cardinality.append({"database_name": self.database, "source_schema": bridge.split(".", 1)[0], "source_object": bridge.split(".", 1)[1], "source_column": "MULTIPLE_FKS", "target_schema": "", "target_object": ", ".join(sorted(targets)), "target_column": "", "classification": "SCHEMA_INFERRED", "confidence": "MEDIUM", "evidence": "table has foreign keys to multiple distinct targets", "evidence_class": "INFERENCE", "likely_cardinality": "N:N_BRIDGE_CANDIDATE", "optionality": "UNKNOWN", "validation_status": "STRUCTURAL_INFERENCE"})
        self.data["relationship_cardinality"] = cardinality
        self.data["orphan_analysis"] = orphans
        _csv(self.artifact("INFERRED_RELATIONSHIPS.csv"), tuple(inferred[0]) if inferred else ("server_name", "database_name", "source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "classification", "confidence", "evidence"), inferred)
        _csv(self.artifact("RELATIONSHIP_CARDINALITY.csv"), tuple(cardinality[0]) if cardinality else ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "likely_cardinality", "validation_status"), cardinality)
        _csv(self.artifact("ORPHAN_ANALYSIS.csv"), tuple(orphans[0]) if orphans else ("source_schema", "source_object", "source_column", "target_schema", "target_object", "target_column", "analysis_status"), orphans)
