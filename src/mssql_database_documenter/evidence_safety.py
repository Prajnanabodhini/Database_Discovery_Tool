"""Fail-closed safety audit for value-bearing run evidence."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from .inventory import safe_path_component
from .redaction import redact_text


SENSITIVE_CATEGORIES = frozenset({"Credential", "PII", "Financial", "Health", "Potentially Sensitive"})
TEXT_EVIDENCE_SUFFIXES = frozenset({".csv", ".html", ".json", ".md", ".mmd", ".sha256", ".sql", ".txt"})
FORBIDDEN_NAMES = frozenset({".env", ".env.local", "credentials.json"})
FORBIDDEN_TRANSIENT_PARTS = frozenset({"__pycache__", ".pytest_cache", "cache", "logs", "temp", "tmp"})
MASKED_TOKEN = re.compile(r"^\[MASKED:[0-9a-f]{16}\]$")


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


def audit_run_evidence(run_root: Path, *, sensitive_values: Iterable[str] = ()) -> EvidenceSafetyAudit:
    """Inspect a run without trusting its generated checklist or manifest claims."""
    run_root = run_root.resolve()
    violations: list[str] = []
    files_scanned = 0
    needles = tuple(str(value) for value in sensitive_values if value and len(str(value)) >= 3)

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
    sensitive = {key: category for key, category in classifications.items() if category in SENSITIVE_CATEGORIES}
    checked = 0

    def check_rows(path: Path, fields: tuple[str, ...], label: str) -> None:
        nonlocal checked
        rows = _read_csv(path)
        if rows and not classifications:
            violations.append(f"{label} exists without sensitivity classification")
            return
        for row_number, row in enumerate(rows, 2):
            category = str(row.get("sensitivity_category") or classifications.get(_identity(row), "Unknown"))
            if category not in SENSITIVE_CATEGORIES:
                continue
            for field in fields:
                value = row.get(field, "")
                if value in (None, ""):
                    continue
                checked += 1
                if not is_safely_masked(value, category):
                    violations.append(f"unmasked {category} value in {label} row {row_number}, field {field}")

    check_rows(run_root / "13_Data_Profiling" / "COLUMN_PROFILE.csv", ("minimum_value", "maximum_value"), "COLUMN_PROFILE.csv")
    check_rows(run_root / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv", ("value",), "LOW_CARDINALITY_VALUES.csv")

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

    unique_violations = tuple(dict.fromkeys(violations))
    checks = {
        "forbidden_files_absent": not any("forbidden credential file" in item for item in unique_violations),
        "transient_paths_absent": not any("transient/internal" in item or "symbolic link" in item for item in unique_violations),
        "configured_secrets_absent": not any("configured sensitive value" in item for item in unique_violations),
        "secret_assignments_redacted": not any("secret assignment" in item for item in unique_violations),
        "profile_values_masked": not any("COLUMN_PROFILE" in item or "LOW_CARDINALITY" in item for item in unique_violations),
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
