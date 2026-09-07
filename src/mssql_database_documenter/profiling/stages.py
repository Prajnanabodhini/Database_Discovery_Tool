"""Profiling, sampling, sensitivity, and size/shape stage ownership."""

from __future__ import annotations

import re
from typing import Any

from ..inventory import safe_path_component
from ..runtime import object_key as _object_key, quote_identifier as _qid
from ..runtime import write_csv as _csv, write_markdown as _md
from . import (
    SENSITIVE_CATEGORIES, build_sample_plan, known_row_estimate as _known_row_estimate,
    evaluate_view_sample_eligibility, sample_failure_status, sanitize_sample_rows,
    within_safety_threshold as _within_safety_threshold,
)
from .policy import (
    NUMERIC_TYPES, SKIP_PROFILE_TYPES, STRING_TYPES,
    mask as _mask, type_family as _type_family,
)


class ProfilingStagesMixin:
    """Domain stages mixed into the sequential orchestrator."""

    @staticmethod
    def _sensitivity_identity(row: dict[str, Any]) -> tuple[str, str, str]:
        return (
            str(row.get("schema_name") or ""),
            str(row.get("object_name") or ""),
            str(row.get("column_name") or ""),
        )

    def _reconcile_profile_sensitivity(self, final_rows: list[dict[str, Any]]) -> None:
        """Apply final classifications to all earlier persisted profile values."""
        final_by_identity = {
            self._sensitivity_identity(row): row
            for row in final_rows
        }

        profile_rows = self.data.get("column_profile")
        if isinstance(profile_rows, list):
            for profile in profile_rows:
                final = final_by_identity.get(self._sensitivity_identity(profile))
                if final is None:
                    continue
                category = str(final["sensitivity_category"])
                profile.update({
                    "sensitivity_category": category,
                    "masking_action": final["masking_action"],
                    "sensitivity_confidence": final["confidence"],
                    "sensitivity_evidence": final["evidence"],
                })
                for field in ("minimum_value", "maximum_value"):
                    profile[field] = _mask(
                        profile.get(field), category, self.mask_salt,
                        self.settings.profile_mask_sensitive_data,
                    )
            _csv(
                self.artifact("COLUMN_PROFILE.csv"),
                tuple(profile_rows[0]) if profile_rows else (
                    "server_name", "database_name", "schema_name", "object_name",
                    "column_name", "profile_status",
                ),
                profile_rows,
            )

        low_cardinality_rows = self.data.get("low_cardinality_values")
        if isinstance(low_cardinality_rows, list):
            for value_row in low_cardinality_rows:
                final = final_by_identity.get(self._sensitivity_identity(value_row))
                if final is None:
                    continue
                category = str(final["sensitivity_category"])
                value_row.update({
                    "sensitivity_category": category,
                    "masking_action": final["masking_action"],
                    "sensitivity_confidence": final["confidence"],
                    "sensitivity_evidence": final["evidence"],
                })
                value_row["value"] = _mask(
                    value_row.get("value"), category, self.mask_salt,
                    self.settings.profile_mask_sensitive_data,
                )
            _csv(
                self.artifact("LOW_CARDINALITY_VALUES.csv"),
                tuple(low_cardinality_rows[0]) if low_cardinality_rows else (
                    "server_name", "database_name", "schema_name", "object_name",
                    "column_name", "value", "value_count", "total_rows",
                ),
                low_cardinality_rows,
            )

    def prompt09_sensitivity(self) -> None:
        rows = []
        descriptions: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            descriptions[key] = descriptions.get(key, "") + " " + str(prop.get("property_value") or "")
        for column in self.data["columns"]:
            key = (str(column["schema_name"]), str(column["object_name"]), str(column["column_name"]))
            evidence_text = f"{column['column_name']} {descriptions.get(key, '')}"
            sample_result = self.data.get("sample_sensitivity", {}).get(key)
            result = sample_result or self.classify_column(
                str(column["column_name"]), schema=str(column["schema_name"]),
                table=str(column["object_name"]), extended_property=descriptions.get(key, ""),
            )
            profile = next((
                item for item in self.data.get("column_profile", ())
                if self._sensitivity_identity(item) == key
            ), None)
            if (
                profile is not None
                and str(profile.get("sensitivity_category") or "") in SENSITIVE_CATEGORIES
                and result.category not in SENSITIVE_CATEGORIES
            ):
                final = {
                    "category": profile["sensitivity_category"],
                    "action": profile["masking_action"],
                    "confidence": profile["sensitivity_confidence"],
                    "evidence": profile["sensitivity_evidence"],
                }
            else:
                final = {
                    "category": result.category,
                    "action": result.action,
                    "confidence": result.confidence,
                    "evidence": result.evidence,
                }
            rows.append({
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": column["schema_name"], "object_name": column["object_name"],
                "column_name": column["column_name"], "data_type": column["data_type"],
                "sensitivity_category": final["category"], "masking_action": final["action"],
                "evidence": final["evidence"],
                "evidence_class": "INFERENCE" if final["category"] not in {"Unknown", "Non-sensitive"} else "UNKNOWN",
                "confidence": final["confidence"],
            })
        self.data["sensitivity"] = rows
        self._reconcile_profile_sensitivity(rows)
        _csv(self.artifact("SENSITIVITY_CLASSIFICATION.csv"), tuple(rows[0]) if rows else (), rows)

    def prompt08_samples(self) -> None:
        if not self.mode_policy.samples:
            _md(self.root / "14_Samples" / "README.md", "# Samples\n\nDisabled by configuration.")
            _csv(self.artifact("MASKING_REPORT.csv"), ("schema_name", "object_name", "object_type", "column_name", "category", "action", "confidence", "evidence"), [])
            _csv(self.artifact("SAMPLE_INDEX.csv"), ("schema_name", "object_name", "object_type", "requested_rows", "returned_rows", "ordering_strategy", "status", "eligibility_reason", "eligibility_evidence", "masked_sensitive_column_count"), [])
            self.data["sample_index"] = []
            return
        columns_by_object: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for column in self.data["columns"]:
            identity = (
                str(column.get("schema_name") or ""), str(column.get("object_name") or ""),
                str(column.get("object_type") or "UNKNOWN"),
            )
            columns_by_object.setdefault(identity, []).append(column)
        masking_rows: list[dict[str, Any]] = []
        sample_index: list[dict[str, Any]] = []
        sample_rows_by_object: dict[str, list[dict[str, Any]]] = {}
        sample_sensitivity: dict[tuple[str, str, str], Any] = {}
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        property_text: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            prop_key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            property_text[prop_key] = property_text.get(prop_key, "") + " " + str(prop.get("property_value") or "")
        views_by_object = {
            (
                str(view.get("schema_name") or "").casefold(),
                str(view.get("object_name") or "").casefold(),
            ): view
            for view in self.data.get("views", [])
        }
        dependency_discovery_complete = (
            "dependencies" in self.data
            and not any(
                str(error.get("query_name") or "").casefold() == "dependencies"
                for error in self.errors
            )
        )
        for (schema, obj, object_type), columns in sorted(columns_by_object.items()):
            key = f"{schema}.{obj}"
            headers = [str(col["column_name"]) for col in sorted(columns, key=lambda item: int(item["column_id"]))]
            primary_keys = [row for row in self.data.get("primary_keys", []) if row.get("schema_name") == schema and row.get("object_name") == obj]
            indexes = [row for row in self.data.get("indexes", []) if row.get("schema_name") == schema and row.get("object_name") == obj]
            view_eligibility = None
            if object_type.strip().upper() == "VIEW":
                view_eligibility = evaluate_view_sample_eligibility(
                    current_database=self.database,
                    schema_name=schema,
                    object_name=obj,
                    view=views_by_object.get((schema.casefold(), obj.casefold())),
                    dependencies=self.data.get("dependencies", ()),
                    static_references=self.data.get("static_references", ()),
                    synonyms=self.data.get("synonyms", ()),
                    dependency_discovery_complete=dependency_discovery_complete,
                )
            plan = build_sample_plan(
                schema_name=schema, object_name=obj, object_type=object_type,
                requested_rows=self.mode_policy.sample_row_limit,
                sample_tables=self.mode_policy.sample_tables, sample_views=self.mode_policy.sample_views,
                sample_large_tables=self.mode_policy.sample_large_tables,
                estimated_rows=_known_row_estimate(sizes, key),
                profile_large_table_threshold=self.mode_policy.profile_row_threshold,
                primary_keys=primary_keys, indexes=indexes,
                view_eligibility=view_eligibility,
            )
            raw_rows: list[dict[str, Any]] = []
            status = plan.status
            if plan.enabled:
                error_count = len(self.errors)
                try:
                    raw_rows = self.fetch_dynamic(
                        plan.sql, prompt="08", stage="samples", schema=schema, obj=obj,
                        query_name="bounded_sample",
                    )
                except Exception as exc:
                    status = sample_failure_status(exc)
                else:
                    if len(self.errors) > error_count:
                        status = sample_failure_status(self.errors[-1].get("sanitized_message", ""))
                    else:
                        status = "SAMPLED" if raw_rows else "EMPTY"
            sanitized = sanitize_sample_rows(
                raw_rows,
                column_names=headers,
                classify=lambda column_name, values: self.classify_column(
                    column_name, schema=schema, table=obj,
                    extended_property=property_text.get((schema, obj, column_name), ""),
                    values=values,
                ),
                salt=self.mask_salt,
            )
            for name, result in sanitized.classifications.items():
                sample_sensitivity[(schema, obj, name)] = result
                masking_rows.append({
                    "schema_name": schema, "object_name": obj, "object_type": object_type,
                    "column_name": name,
                    "category": result.category, "action": result.action,
                    "confidence": result.confidence, "evidence": result.evidence,
                })
            safe_rows = list(sanitized.rows)
            _csv(self.root / "14_Samples" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.csv", headers, safe_rows)
            sample_rows_by_object[key] = safe_rows
            sample_index.append({
                "schema_name": schema, "object_name": obj, "object_type": object_type,
                "requested_rows": plan.requested_rows, "returned_rows": len(safe_rows),
                "ordering_strategy": plan.ordering_strategy, "status": status,
                "eligibility_reason": plan.eligibility_reason,
                "eligibility_evidence": plan.eligibility_evidence,
                "masked_sensitive_column_count": sanitized.masked_sensitive_column_count,
            })
        self.data["masking"] = masking_rows
        self.data["sample_rows"] = sample_rows_by_object
        self.data["sample_sensitivity"] = sample_sensitivity
        self.data["sample_index"] = sample_index
        _csv(self.artifact("MASKING_REPORT.csv"), ("schema_name", "object_name", "object_type", "column_name", "category", "action", "confidence", "evidence"), masking_rows)
        _csv(self.artifact("SAMPLE_INDEX.csv"), ("schema_name", "object_name", "object_type", "requested_rows", "returned_rows", "ordering_strategy", "status", "eligibility_reason", "eligibility_evidence", "masked_sensitive_column_count"), sample_index)

    def prompt07_profile(self) -> None:
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        property_text: dict[tuple[str, str, str], str] = {}
        for prop in self.data.get("extended_properties", []):
            prop_key = (str(prop.get("schema_name") or ""), str(prop.get("object_name") or ""), str(prop.get("column_name") or ""))
            property_text[prop_key] = property_text.get(prop_key, "") + " " + str(prop.get("property_value") or "")
        profile_rows: list[dict[str, Any]] = []
        low_cardinality_rows: list[dict[str, Any]] = []
        for column in self.data["columns"]:
            if column.get("object_type") != "USER_TABLE":
                continue
            schema, table, name = str(column["schema_name"]), str(column["object_name"]), str(column["column_name"])
            dtype = str(column.get("data_type") or "").lower()
            description = property_text.get((schema, table, name), "")
            classification = self.classify_column(
                name, schema=schema, table=table, extended_property=description,
            )
            category, masking_action = classification.category, classification.action
            table_key = f"{schema}.{table}"
            known_estimate = _known_row_estimate(sizes, table_key)
            estimated: int | str = known_estimate if known_estimate is not None else ""
            base = {
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": schema, "object_name": table, "column_name": name,
                "data_type": dtype, "estimated_table_rows": estimated,
                "sensitivity_category": category, "masking_action": masking_action,
                "sensitivity_confidence": classification.confidence,
                "sensitivity_evidence": classification.evidence,
                "total_rows": "", "non_null_count": "", "null_count": "",
                "null_percent": "", "distinct_count": "", "distinct_percent": "", "minimum_value": "", "maximum_value": "",
                "empty_string_count": "", "whitespace_string_count": "",
                "zero_count": "", "negative_count": "", "minimum_length": "", "maximum_length": "",
                "average_numeric": "", "standard_deviation_numeric": "",
                "true_count": "", "false_count": "",
                "candidate_unique": "", "all_null": "", "constant_value": "",
                "profile_status": "",
            }
            if known_estimate is None:
                base["profile_status"] = "SKIPPED_ROW_ESTIMATE_UNAVAILABLE"
            elif not _within_safety_threshold(sizes, table_key, self.mode_policy.profile_row_threshold):
                base["profile_status"] = "SKIPPED_FOR_SAFETY_LARGE_TABLE"
            elif dtype in SKIP_PROFILE_TYPES:
                base["profile_status"] = "SKIPPED_FOR_SAFETY_OR_TYPE"
            elif column.get("is_computed"):
                base["profile_status"] = "SKIPPED_COMPUTED"
            else:
                qcol = _qid(name)
                extras = []
                if dtype in STRING_TYPES:
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} = '' THEN 1 ELSE 0 END) AS empty_string_count",
                        f"SUM(CASE WHEN {qcol} IS NOT NULL AND LTRIM(RTRIM({qcol})) = '' THEN 1 ELSE 0 END) AS whitespace_string_count",
                        f"MIN(LEN({qcol})) AS minimum_length", f"MAX(LEN({qcol})) AS maximum_length",
                    ))
                if dtype in NUMERIC_TYPES or dtype == "bit":
                    extras.append(f"SUM(CASE WHEN {qcol} = 0 THEN 1 ELSE 0 END) AS zero_count")
                if dtype in NUMERIC_TYPES:
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} < 0 THEN 1 ELSE 0 END) AS negative_count",
                        f"AVG(CONVERT(float, {qcol})) AS average_numeric",
                        f"STDEV(CONVERT(float, {qcol})) AS standard_deviation_numeric",
                    ))
                if dtype == "bit":
                    extras.extend((
                        f"SUM(CASE WHEN {qcol} = 1 THEN 1 ELSE 0 END) AS true_count",
                        f"SUM(CASE WHEN {qcol} = 0 THEN 1 ELSE 0 END) AS false_count",
                    ))
                extra_sql = (", " + ", ".join(extras)) if extras else ""
                distinct_sql = f"COUNT_BIG(DISTINCT {qcol})" if self.mode_policy.low_cardinality_limit else "CAST(NULL AS bigint)"
                sql = (
                    f"SELECT COUNT_BIG(*) AS total_rows, COUNT_BIG({qcol}) AS non_null_count, "
                    f"{distinct_sql} AS distinct_count, "
                    f"MIN(CONVERT(nvarchar(4000), {qcol})) AS minimum_value, "
                    f"MAX(CONVERT(nvarchar(4000), {qcol})) AS maximum_value{extra_sql} "
                    f"FROM {_qid(schema)}.{_qid(table)}"
                )
                result = self.fetch_dynamic(sql, prompt="07", stage="column_profile", schema=schema, obj=table, query_name=name)
                if result:
                    first = dict(result[0])
                    classification = self.classify_column(
                        name, schema=schema, table=table, extended_property=description,
                        values=(first.get("minimum_value"), first.get("maximum_value")),
                    )
                    category, masking_action = classification.category, classification.action
                    base.update({
                        "sensitivity_category": category, "masking_action": masking_action,
                        "sensitivity_confidence": classification.confidence,
                        "sensitivity_evidence": classification.evidence,
                    })
                    first["minimum_value"] = _mask(first.get("minimum_value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data)
                    first["maximum_value"] = _mask(first.get("maximum_value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data)
                    base.update(first)
                    total = int(first["total_rows"]); non_null = int(first["non_null_count"])
                    distinct_value = first.get("distinct_count")
                    distinct_count = int(distinct_value) if distinct_value is not None else None
                    base["null_count"] = total - non_null
                    base["null_percent"] = round(((total - non_null) * 100.0 / total), 4) if total else 0.0
                    base["distinct_percent"] = round((distinct_count * 100.0 / non_null), 4) if distinct_count is not None and non_null else ""
                    base["candidate_unique"] = (non_null == distinct_count and total == non_null) if distinct_count is not None else "NOT_EVALUATED"
                    base["all_null"] = int(first["non_null_count"]) == 0
                    base["constant_value"] = (distinct_count <= 1 and non_null > 0) if distinct_count is not None else "NOT_EVALUATED"
                    base["profile_status"] = "PROFILED"
                    if self.mode_policy.low_cardinality_limit and distinct_count is not None and distinct_count <= self.mode_policy.low_cardinality_limit:
                        distribution_sql = (
                            f"SELECT CONVERT(nvarchar(4000), {qcol}) AS value, COUNT_BIG(*) AS value_count "
                            f"FROM {_qid(schema)}.{_qid(table)} GROUP BY {qcol} ORDER BY value_count DESC"
                        )
                        distribution = self.fetch_dynamic(distribution_sql, prompt="07", stage="low_cardinality", schema=schema, obj=table, query_name=name)
                        classification = self.classify_column(
                            name, schema=schema, table=table, extended_property=description,
                            values=(item.get("value") for item in distribution),
                        )
                        category, masking_action = classification.category, classification.action
                        base.update({
                            "sensitivity_category": category, "masking_action": masking_action,
                            "sensitivity_confidence": classification.confidence,
                            "sensitivity_evidence": classification.evidence,
                        })
                        for value_row in distribution[: self.mode_policy.low_cardinality_limit + 1]:
                            low_cardinality_rows.append({
                                "server_name": "[SANITIZED]", "database_name": self.database,
                                "schema_name": schema, "object_name": table, "column_name": name,
                                "sensitivity_category": category, "masking_action": masking_action,
                                "sensitivity_confidence": classification.confidence,
                                "sensitivity_evidence": classification.evidence,
                                "value": _mask(value_row.get("value"), category, self.mask_salt, self.settings.profile_mask_sensitive_data),
                                "value_count": value_row.get("value_count"),
                                "total_rows": first["total_rows"],
                                "value_percent": round((int(value_row.get("value_count") or 0) * 100.0 / total), 4) if total else 0.0,
                            })
                else:
                    base["profile_status"] = "ERROR_RECORDED"
            profile_rows.append(base)
        self.data["column_profile"] = profile_rows
        self.data["low_cardinality_values"] = low_cardinality_rows
        _csv(self.artifact("COLUMN_PROFILE.csv"), tuple(profile_rows[0]) if profile_rows else ("server_name", "database_name", "schema_name", "object_name", "column_name", "profile_status"), profile_rows)
        _csv(self.artifact("LOW_CARDINALITY_VALUES.csv"), tuple(low_cardinality_rows[0]) if low_cardinality_rows else ("server_name", "database_name", "schema_name", "object_name", "column_name", "value", "value_count", "total_rows"), low_cardinality_rows)

    def prompt06_size_shape(self) -> None:
        columns = self.data["columns"]
        sizes = {_object_key(row): row for row in self.data.get("table_sizes", [])}
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in columns:
            if row.get("object_type") == "USER_TABLE":
                grouped.setdefault(_object_key(row), []).append(row)
        rows = []
        for key, cols in sorted(grouped.items()):
            size = sizes.get(key, {})
            known_estimate = _known_row_estimate(sizes, key)
            estimated_rows: int | str = known_estimate if known_estimate is not None else ""
            row_count: int | str = estimated_rows
            row_count_type = "ESTIMATED"
            if (
                self.mode_policy.exact_counts
                and _within_safety_threshold(sizes, key, self.mode_policy.exact_count_ceiling)
            ):
                schema_name, object_name = key.split(".", 1)
                exact = self.fetch_dynamic(
                    f"SELECT COUNT_BIG(*) AS exact_rows FROM {_qid(schema_name)}.{_qid(object_name)}",
                    prompt="06", stage="exact_row_count", schema=schema_name, obj=object_name,
                    query_name="configured_exact_row_count",
                )
                if exact:
                    row_count = int(exact[0].get("exact_rows") or 0)
                    row_count_type = "EXACT"
                    size["row_count"] = row_count
                    size["row_count_type"] = row_count_type
            family_counts = {family: 0 for family in ("STRING", "NUMERIC", "DATE_TIME", "BINARY", "OTHER")}
            for col in cols:
                family_counts[_type_family(str(col.get("data_type") or ""))] += 1
            rows.append({
                "server_name": "[SANITIZED]", "database_name": self.database,
                "schema_name": cols[0]["schema_name"], "object_name": cols[0]["object_name"],
                "estimated_rows": estimated_rows, "row_count": row_count, "column_count": len(cols),
                "nullable_columns": sum(bool(c.get("is_nullable")) for c in cols),
                "identity_columns": sum(bool(c.get("is_identity")) for c in cols),
                "computed_columns": sum(bool(c.get("is_computed")) for c in cols),
                "identifier_columns": sum(bool(re.search(r"(^id$|id$|_id$)", str(c.get("column_name") or ""), re.I)) for c in cols),
                "string_columns": family_counts["STRING"], "numeric_columns": family_counts["NUMERIC"],
                "date_time_columns": family_counts["DATE_TIME"], "binary_columns": family_counts["BINARY"],
                "other_type_columns": family_counts["OTHER"],
                "large_object_columns": sum(str(c.get("data_type", "")).lower() in SKIP_PROFILE_TYPES for c in cols),
                "evidence_type": "FACT", "row_count_type": row_count_type,
            })
        self.data["table_shape"] = rows
        self.data["table_sizes"] = list(sizes.values())
        if self.data["table_sizes"]:
            _csv(self.artifact("TABLE_SIZE_PROFILE.csv"), tuple(self.data["table_sizes"][0]), self.data["table_sizes"])
        _csv(self.artifact("TABLE_SHAPE_PROFILE.csv"), tuple(rows[0]) if rows else ("server_name", "database_name", "schema_name", "object_name", "estimated_rows", "column_count"), rows)
