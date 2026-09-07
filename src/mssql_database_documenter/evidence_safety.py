"""Fail-closed safety audit for value-bearing run evidence."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable

from .inventory import safe_path_component
from .profiling.sensitivity import SENSITIVE_CATEGORIES, classify_sensitivity
from .redaction import redact_text


TEXT_EVIDENCE_SUFFIXES = frozenset({".csv", ".html", ".json", ".md", ".mmd", ".sha256", ".sql", ".txt"})
FORBIDDEN_NAMES = frozenset({".env", ".env.local", "credentials.json"})
FORBIDDEN_TRANSIENT_PARTS = frozenset({"__pycache__", ".pytest_cache", "cache", "logs", "temp", "tmp"})
MASKED_TOKEN = re.compile(r"^\[MASKED:[0-9a-f]{16}\]$")
VALID_GIT_PROFILE_POLICIES = frozenset({"mask_unknown_text", "aggregate_only"})
NUMERIC_PROFILE_TYPES = frozenset({
    "bigint", "bit", "decimal", "float", "int", "money", "numeric",
    "real", "smallint", "smallmoney", "tinyint",
})
DATE_PROFILE_TYPES = frozenset({
    "date", "datetime", "datetime2", "datetimeoffset", "smalldatetime", "time",
})
BINARY_PROFILE_TYPES = frozenset({"binary", "image", "rowversion", "timestamp", "varbinary"})


@dataclass(frozen=True, slots=True)
class EvidenceSafetyAudit:
    files_scanned: int
    classified_columns: int
    sensitive_columns: int
    sensitive_values_checked: int
    checks: dict[str, bool]
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.violations and all(self.checks.values())

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "PASS" if self.passed else "FAIL",
            "files_scanned": self.files_scanned,
            "classified_columns": self.classified_columns,
            "sensitive_columns": self.sensitive_columns,
            "sensitive_values_checked": self.sensitive_values_checked,
            "checks": self.checks,
            "violations": list(self.violations),
        }


def is_safely_masked(value: object, category: str) -> bool:
    """Return whether a persisted sensitive value uses the required safe token."""
    text = "" if value is None else str(value).strip()
    if not text:
        return True
    if category == "Credential":
        return text == "[REDACTED]"
    return text == "[REDACTED]" or bool(MASKED_TOKEN.fullmatch(text))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _identity(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("schema_name") or "").casefold(),
        str(row.get("object_name") or "").casefold(),
        str(row.get("column_name") or "").casefold(),
    )


def audit_run_evidence(
    run_root: Path,
    *,
    sensitive_values: Iterable[str] = (),
    require_git_export_policy: bool = False,
) -> EvidenceSafetyAudit:
    """Inspect a run without trusting its generated checklist or manifest claims."""
    run_root = run_root.resolve()
    violations: list[str] = []
    files_scanned = 0
    needles = tuple(str(value) for value in sensitive_values if value and len(str(value)) >= 3)
    git_policy: dict[str, object] = {}
    git_policy_path = run_root / "99_Git_Handoff" / "GIT_EXPORT_POLICY.json"
    if git_policy_path.is_file():
        try:
            loaded_policy = json.loads(git_policy_path.read_text(encoding="utf-8-sig"))
            if isinstance(loaded_policy, dict):
                git_policy = loaded_policy
            else:
                violations.append("Git export policy record is not a JSON object")
        except (OSError, ValueError, TypeError):
            violations.append("Git export policy record is unreadable")
    elif require_git_export_policy:
        violations.append("Git export profile-value policy record is required")
    profile_policy = str(git_policy.get("profile_value_policy") or "")
    if git_policy and profile_policy not in VALID_GIT_PROFILE_POLICIES:
        violations.append("Git export profile-value policy is missing or invalid")
    if git_policy and git_policy.get("source_evidence_mutated") is not False:
        violations.append("Git export policy does not affirm source evidence mutated = false")

    for path in run_root.rglob("*"):
        relative = path.relative_to(run_root)
        if path.is_symlink():
            violations.append(f"symbolic link is not allowed: {relative.as_posix()}")
            continue
        if any(part.casefold() in FORBIDDEN_TRANSIENT_PARTS for part in relative.parts):
            violations.append(f"transient/internal path is not allowed: {relative.as_posix()}")
        if not path.is_file():
            continue
        files_scanned += 1
        if path.name.casefold() in FORBIDDEN_NAMES:
            violations.append(f"forbidden credential file: {relative.as_posix()}")
        if path.suffix.casefold() not in TEXT_EVIDENCE_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(value.casefold() in text.casefold() for value in needles):
            violations.append(f"configured sensitive value found: {relative.as_posix()}")
        if redact_text(text, sensitive_values=needles) != text:
            violations.append(f"potential unredacted secret assignment found: {relative.as_posix()}")

    sensitivity_path = run_root / "13_Data_Profiling" / "SENSITIVITY_CLASSIFICATION.csv"
    sensitivity_rows = _read_csv(sensitivity_path)
    classifications = {
        _identity(row): str(row.get("sensitivity_category") or "Unknown")
        for row in sensitivity_rows
    }
    classification_evidence = {
        _identity(row): str(row.get("evidence") or row.get("sensitivity_evidence") or "")
        for row in sensitivity_rows
    }
    sensitive = {key: category for key, category in classifications.items() if category in SENSITIVE_CATEGORIES}
    checked = 0
    staged_profile_masks = 0
    profile_data_types = {
        _identity(row): str(row.get("data_type") or "").casefold()
        for row in _read_csv(run_root / "13_Data_Profiling" / "COLUMN_PROFILE.csv")
    }

    def effective_category(row: dict[str, str], values: Iterable[object] = ()) -> str:
        identity = _identity(row)
        catalogued = classifications.get(identity, "Unknown")
        evidence = classification_evidence.get(identity, "")
        if catalogued in SENSITIVE_CATEGORIES:
            return catalogued
        if catalogued == "Non-sensitive" and evidence.upper().startswith("OVERRIDE:"):
            return catalogued
        stored = str(row.get("sensitivity_category") or catalogued)
        if stored in SENSITIVE_CATEGORIES:
            return stored
        detected = classify_sensitivity(
            str(row.get("column_name") or ""), schema=str(row.get("schema_name") or ""),
            table=str(row.get("object_name") or ""), values=values,
        )
        return detected.category if detected.category in SENSITIVE_CATEGORIES else stored

    def check_rows(path: Path, fields: tuple[str, ...], label: str) -> None:
        nonlocal checked, staged_profile_masks
        rows = _read_csv(path)
        if rows and not classifications:
            violations.append(f"{label} exists without sensitivity classification")
            return
        for row_number, row in enumerate(rows, 2):
            category = effective_category(row, (row.get(field, "") for field in fields))
            identity = _identity(row)
            evidence = classification_evidence.get(identity) or str(row.get("sensitivity_evidence") or "")
            data_type = str(row.get("data_type") or profile_data_types.get(identity, "")).casefold()
            for field in fields:
                value = row.get(field, "")
                if value in (None, ""):
                    continue
                if profile_policy == "aggregate_only":
                    violations.append(f"profile value retained under aggregate_only in {label} row {row_number}, field {field}")
                    continue
                if category in SENSITIVE_CATEGORIES:
                    checked += 1
                    if not is_safely_masked(value, category):
                        violations.append(f"unmasked {category} value in {label} row {row_number}, field {field}")
                    elif profile_policy:
                        staged_profile_masks += 1
                    continue
                if profile_policy != "mask_unknown_text":
                    continue
                text = str(value).strip()
                if text == "[REDACTED]" or text == "[BINARY_REDACTED]" or MASKED_TOKEN.fullmatch(text):
                    staged_profile_masks += 1
                elif data_type in BINARY_PROFILE_TYPES:
                    violations.append(f"unredacted binary profile value in {label} row {row_number}, field {field}")
                elif category == "Non-sensitive" and evidence.upper().startswith("OVERRIDE:"):
                    continue
                elif data_type in NUMERIC_PROFILE_TYPES or data_type in DATE_PROFILE_TYPES:
                    continue
                else:
                    violations.append(f"unmasked unknown text profile value in {label} row {row_number}, field {field}")

    def verify_git_policy_record() -> None:
        if not git_policy:
            return
        manifest_path = run_root / "00_Run_Metadata" / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, TypeError):
            violations.append("Git export manifest is unreadable during policy verification")
            return
        if manifest.get("git_export") != git_policy:
            violations.append("Git export manifest policy does not match the independent policy record")
        try:
            recorded_masked = int(git_policy.get("profile_values_masked", -1))
            recorded_omitted = int(git_policy.get("profile_values_omitted", -1))
        except (TypeError, ValueError):
            violations.append("Git export profile-value counters are invalid")
            return
        if recorded_masked < 0 or recorded_omitted < 0:
            violations.append("Git export profile-value counters are invalid")
        if profile_policy == "mask_unknown_text" and recorded_masked != staged_profile_masks:
            violations.append("Git export masked profile-value count does not match staged evidence")
        if profile_policy == "aggregate_only" and (
            recorded_masked != 0 or git_policy.get("profile_value_fields_withheld") is not True
            or not git_policy.get("withheld_profile_fields")
        ):
            violations.append("Git export aggregate-only policy marker or masked counter is inaccurate")

    check_rows(run_root / "13_Data_Profiling" / "COLUMN_PROFILE.csv", ("minimum_value", "maximum_value"), "COLUMN_PROFILE.csv")
    check_rows(run_root / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv", ("value",), "LOW_CARDINALITY_VALUES.csv")
    verify_git_policy_record()

    masking_rows = _read_csv(run_root / "14_Samples" / "MASKING_REPORT.csv")
    sample_groups: dict[tuple[str, str], dict[str, str]] = {}
    for row in masking_rows:
        category = str(row.get("category") or "Unknown")
        if category not in SENSITIVE_CATEGORIES:
            continue
        group = (str(row.get("schema_name") or ""), str(row.get("object_name") or ""))
        sample_groups.setdefault(group, {})[str(row.get("column_name") or "")] = category
    for (schema, obj), columns in sample_groups.items():
        sample_path = run_root / "14_Samples" / f"{safe_path_component(schema)}__{safe_path_component(obj)}.csv"
        for row_number, row in enumerate(_read_csv(sample_path), 2):
            for column, category in columns.items():
                value = row.get(column, "")
                if value in (None, ""):
                    continue
                checked += 1
                if not is_safely_masked(value, category):
                    violations.append(f"unmasked {category} sample in {sample_path.name} row {row_number}, column {column}")

    samples_root = run_root / "14_Samples"
    control_names = {"masking_report.csv", "sample_index.csv"}
    for sample_path in samples_root.glob("*.csv") if samples_root.is_dir() else ():
        if sample_path.name.casefold() in control_names:
            continue
        for row_number, row in enumerate(_read_csv(sample_path), 2):
            for column, value in row.items():
                if value in (None, ""):
                    continue
                category = next((
                    stored for (schema, obj), mapping in sample_groups.items()
                    for name, stored in mapping.items()
                    if sample_path.name.casefold() == f"{safe_path_component(schema)}__{safe_path_component(obj)}.csv".casefold()
                    and name.casefold() == column.casefold()
                ), "Unknown")
                detected = classify_sensitivity(column, values=(value,))
                if category not in SENSITIVE_CATEGORIES and detected.category in SENSITIVE_CATEGORIES:
                    category = detected.category
                if category in SENSITIVE_CATEGORIES:
                    checked += 1
                    if not is_safely_masked(value, category):
                        violations.append(f"unmasked {category} sample in {sample_path.name} row {row_number}, column {column}")

    unique_violations = tuple(dict.fromkeys(violations))
    checks = {
        "forbidden_files_absent": not any("forbidden credential file" in item for item in unique_violations),
        "transient_paths_absent": not any("transient/internal" in item or "symbolic link" in item for item in unique_violations),
        "configured_secrets_absent": not any("configured sensitive value" in item for item in unique_violations),
        "secret_assignments_redacted": not any("secret assignment" in item for item in unique_violations),
        "profile_values_masked": not any(
            "COLUMN_PROFILE" in item or "LOW_CARDINALITY" in item or "profile value" in item
            for item in unique_violations
        ),
        "git_profile_policy_valid": not any("profile-value policy" in item for item in unique_violations),
        "git_profile_policy_record_accurate": not any(
            "manifest policy" in item or "profile-value count" in item
            or "aggregate-only policy marker" in item or "source evidence mutated" in item
            for item in unique_violations
        ),
        "sample_values_masked": not any(" sample in " in item for item in unique_violations),
    }
    return EvidenceSafetyAudit(
        files_scanned=files_scanned,
        classified_columns=len(classifications),
        sensitive_columns=len(sensitive),
        sensitive_values_checked=checked,
        checks=checks,
        violations=unique_violations,
    )
