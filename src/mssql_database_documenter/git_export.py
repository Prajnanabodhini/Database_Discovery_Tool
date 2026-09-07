"""Explicit, policy-controlled Git-export creation for an existing real run."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Iterable

from .evidence_safety import audit_run_evidence
from .inventory import safe_path_component
from .path_safety import (
    UnsafeDestinationError,
    ensure_contained_directory,
    is_reparse_point,
    new_contained_path,
)
from .profiling.sensitivity import SENSITIVE_CATEGORIES, classify_sensitivity, mask_value
from .redaction import redact_text


class GitExportError(ValueError):
    pass


ALLOWED_EVIDENCE_SUFFIXES = frozenset({".csv", ".html", ".json", ".md", ".mmd", ".sha256", ".sql", ".txt"})
FORBIDDEN_TRANSIENT_PARTS = frozenset({"__pycache__", ".pytest_cache", "cache", "logs", "temp", "tmp"})
VALID_SAMPLE_POLICIES = frozenset({"exclude", "masked_only"})
VALID_PROFILE_VALUE_POLICIES = frozenset({"mask_unknown_text", "aggregate_only"})
SAMPLE_CONTROL_FILES = frozenset({"masking_report.csv", "sample_index.csv"})
PROFILE_VALUE_FILES = {
    "column_profile.csv": ("minimum_value", "maximum_value"),
    "low_cardinality_values.csv": ("value",),
}
NUMERIC_PROFILE_TYPES = frozenset({
    "bigint", "bit", "decimal", "float", "int", "money", "numeric",
    "real", "smallint", "smallmoney", "tinyint",
})
DATE_PROFILE_TYPES = frozenset({
    "date", "datetime", "datetime2", "datetimeoffset", "smalldatetime", "time",
})
BINARY_PROFILE_TYPES = frozenset({"binary", "image", "rowversion", "timestamp", "varbinary"})


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _is_sample_payload(relative: Path) -> bool:
    return (
        len(relative.parts) == 2
        and relative.parts[0].casefold() == "14_samples"
        and relative.suffix.casefold() == ".csv"
        and relative.name.casefold() not in SAMPLE_CONTROL_FILES
    )


def _masking_categories(run_root: Path) -> dict[tuple[str, str], str]:
    report = run_root / "14_Samples" / "MASKING_REPORT.csv"
    if not report.is_file():
        return {}
    with report.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (
            f"{safe_path_component(str(row.get('schema_name') or ''))}__{safe_path_component(str(row.get('object_name') or ''))}.csv".casefold(),
            str(row.get("column_name") or "").casefold(),
        ): str(row.get("category") or "Potentially Sensitive")
        for row in rows
    }


def _profile_identity(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("schema_name") or "").casefold(),
        str(row.get("object_name") or "").casefold(),
        str(row.get("column_name") or "").casefold(),
    )


def _profile_classifications(run_root: Path) -> dict[tuple[str, str, str], tuple[str, str]]:
    path = run_root / "13_Data_Profiling" / "SENSITIVITY_CLASSIFICATION.csv"
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        _profile_identity(row): (
            str(row.get("sensitivity_category") or "Unknown"),
            str(row.get("evidence") or row.get("sensitivity_evidence") or ""),
        )
        for row in rows
    }


def _profile_data_types(run_root: Path) -> dict[tuple[str, str, str], str]:
    path = run_root / "13_Data_Profiling" / "COLUMN_PROFILE.csv"
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            _profile_identity(row): str(row.get("data_type") or "").casefold()
            for row in csv.DictReader(handle)
        }


def _sanitize_profile_values(
    staged_root: Path,
    *,
    policy: str,
    salt: str,
    classifications: dict[tuple[str, str, str], tuple[str, str]],
    data_types: dict[tuple[str, str, str], str],
) -> tuple[int, int]:
    """Apply the stricter publication policy to staged profile CSVs only."""
    masked = 0
    omitted = 0
    profile_root = staged_root / "13_Data_Profiling"
    for filename, value_fields in PROFILE_VALUE_FILES.items():
        path = profile_root / filename.upper()
        if not path.is_file():
            path = next(
                (candidate for candidate in profile_root.glob("*.csv") if candidate.name.casefold() == filename),
                path,
            )
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = tuple(reader.fieldnames or ())
            rows = list(reader)
        for row in rows:
            identity = _profile_identity(row)
            catalog_category, catalog_evidence = classifications.get(identity, ("Unknown", ""))
            row_category = str(row.get("sensitivity_category") or catalog_category)
            category = catalog_category if identity in classifications else row_category
            evidence = catalog_evidence or str(row.get("sensitivity_evidence") or "")
            data_type = str(row.get("data_type") or data_types.get(identity, "")).casefold()
            for field in value_fields:
                value = row.get(field, "")
                if value in (None, ""):
                    continue
                if policy == "aggregate_only":
                    row[field] = ""
                    omitted += 1
                    continue
                reviewed_non_sensitive = (
                    category == "Non-sensitive" and evidence.upper().startswith("OVERRIDE:")
                )
                if not reviewed_non_sensitive:
                    detected = classify_sensitivity(
                        str(row.get("column_name") or ""),
                        schema=str(row.get("schema_name") or ""),
                        table=str(row.get("object_name") or ""),
                        values=(value,),
                    )
                    if category not in SENSITIVE_CATEGORIES and detected.category in SENSITIVE_CATEGORIES:
                        category = detected.category
                if category == "Credential":
                    row[field] = "[REDACTED]"
                    masked += 1
                elif category in SENSITIVE_CATEGORIES:
                    row[field] = str(mask_value(value, category=category, salt=salt))
                    masked += 1
                elif data_type in BINARY_PROFILE_TYPES:
                    row[field] = "[BINARY_REDACTED]"
                    masked += 1
                elif reviewed_non_sensitive:
                    continue
                elif data_type in NUMERIC_PROFILE_TYPES or data_type in DATE_PROFILE_TYPES:
                    continue
                else:
                    row[field] = str(mask_value(value, category="Potentially Sensitive", salt=salt))
                    masked += 1
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return masked, omitted


def _sanitize_sample(path: Path, *, salt: str, categories: dict[tuple[str, str], str]) -> None:
    """Mask every non-empty sample cell in a staged copy; never edit source evidence."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        rows = list(reader)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            sanitized: dict[str, str] = {}
            for column in fieldnames:
                value = row.get(column, "")
                category = categories.get((path.name.casefold(), column.casefold()), "Potentially Sensitive")
                sanitized[column] = "" if value in (None, "") else mask_value(value, category=category, salt=salt)
            writer.writerow(sanitized)


def _refresh_manifest_and_checksums(
    staged_root: Path,
    *,
    policy: str,
    omitted: list[str],
    sanitized: list[str],
    profile_value_policy: str,
    profile_values_masked: int,
    profile_values_omitted: int,
) -> None:
    metadata_root = staged_root / "00_Run_Metadata"
    handoff_root = staged_root / "99_Git_Handoff"
    metadata_root.mkdir(parents=True, exist_ok=True)
    handoff_root.mkdir(parents=True, exist_ok=True)

    policy_record = {
        "sample_policy": policy,
        "raw_sample_payloads_included": False,
        "sample_payloads_omitted": omitted,
        "sample_payloads_sanitized": sanitized,
        "profile_value_policy": profile_value_policy,
        "profile_values_masked": profile_values_masked,
        "profile_values_omitted": profile_values_omitted,
        "profile_value_fields_withheld": profile_value_policy == "aggregate_only",
        "withheld_profile_fields": (
            [
                "13_Data_Profiling/COLUMN_PROFILE.csv:minimum_value",
                "13_Data_Profiling/COLUMN_PROFILE.csv:maximum_value",
                "13_Data_Profiling/LOW_CARDINALITY_VALUES.csv:value",
            ]
            if profile_value_policy == "aggregate_only" else []
        ),
        "source_evidence_mutated": False,
    }
    (handoff_root / "GIT_EXPORT_POLICY.json").write_text(
        json.dumps(policy_record, indent=2) + "\n", encoding="utf-8"
    )

    checklist_path = handoff_root / "SAFE_TO_COMMIT_CHECKLIST.md"
    existing = checklist_path.read_text(encoding="utf-8-sig") if checklist_path.is_file() else "# Safe to Commit Checklist\n"
    export_section = (
        "\n## Git export policy\n\n"
        f"- [x] Sample policy: `{policy}`\n"
        "- [x] Raw sample payloads are not included\n"
        f"- [x] Sample payloads omitted: {len(omitted)}\n"
        f"- [x] Sample payloads sanitized in the staged copy: {len(sanitized)}\n"
        f"- [x] Profile-value policy: `{profile_value_policy}`\n"
        f"- [x] Profile values masked in the staged copy: {profile_values_masked}\n"
        f"- [x] Profile values omitted from the staged copy: {profile_values_omitted}\n"
        f"- [x] Profile extrema and distribution labels withheld: {profile_value_policy == 'aggregate_only'}\n"
        "- [x] Source run evidence was not mutated\n"
        "- [x] Independent fail-closed audit passed before publication\n"
    )
    checklist_path.write_text(existing.rstrip() + "\n" + export_section, encoding="utf-8")

    manifest_path = metadata_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest["git_export"] = policy_record
    configuration = manifest.get("configuration")
    if isinstance(configuration, dict):
        configuration["git_export_sample_policy"] = policy
        configuration["git_export_profile_value_policy"] = profile_value_policy
    checksum_path = metadata_root / "checksums.sha256"
    files = sorted(
        set(
            path.relative_to(staged_root).as_posix()
            for path in staged_root.rglob("*")
            if path.is_file()
        )
        | {manifest_path.relative_to(staged_root).as_posix(), checksum_path.relative_to(staged_root).as_posix()}
    )
    manifest["files"] = files
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")

    checksum_lines = []
    for path in sorted(path for path in staged_root.rglob("*") if path.is_file() and path != checksum_path):
        checksum_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(staged_root).as_posix()}")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def create_git_export(
    run_root: Path,
    *,
    output_root: Path,
    git_export_root: Path,
    sensitive_values: Iterable[str] = (),
    sample_policy: str = "exclude",
    profile_value_policy: str = "mask_unknown_text",
) -> Path:
    """Build and audit an isolated export; publish it only after every gate passes."""
    run_root = run_root.resolve()
    sample_policy = sample_policy.strip().casefold()
    if sample_policy not in VALID_SAMPLE_POLICIES:
        raise GitExportError("Git export sample policy must be exclude or masked_only; raw is never allowed")
    profile_value_policy = profile_value_policy.strip().casefold()
    if profile_value_policy not in VALID_PROFILE_VALUE_POLICIES:
        raise GitExportError(
            "Git export profile-value policy must be mask_unknown_text or aggregate_only; raw is never allowed"
        )
    if not _contained(output_root, run_root) or not run_root.is_dir():
        raise GitExportError("Selected run is outside the configured output root")
    manifest_path = run_root / "00_Run_Metadata" / "manifest.json"
    if not manifest_path.is_file():
        raise GitExportError("Selected directory is not a real manifested run")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    database = safe_path_component(str(manifest.get("database") or run_root.parent.name))
    run_id = safe_path_component(str(manifest.get("run_id") or run_root.name.removeprefix("run_")))
    forbidden = {".env", ".env.local", "credentials.json"}
    needles = tuple(str(value) for value in sensitive_values if value and len(str(value)) >= 3)
    source_files: list[tuple[Path, Path]] = []
    for path in run_root.rglob("*"):
        relative = path.relative_to(run_root)
        if is_reparse_point(path):
            raise GitExportError(f"Run contains a symbolic link or reparse point: {relative.as_posix()}")
        if any(part.casefold() in FORBIDDEN_TRANSIENT_PARTS for part in relative.parts):
            raise GitExportError(f"Run contains a transient/internal path: {relative.as_posix()}")
        if not path.is_file():
            continue
        if path.name.casefold() in forbidden:
            raise GitExportError("Run contains a forbidden credential file")
        if path.suffix.casefold() not in ALLOWED_EVIDENCE_SUFFIXES:
            raise GitExportError(f"Run contains a non-evidence file type: {path.name}")
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(value.casefold() in text.casefold() for value in needles):
            raise GitExportError(f"Configured sensitive value found in {path.name}")
        if redact_text(text, sensitive_values=needles) != text:
            raise GitExportError(f"Potential unredacted secret assignment found in {path.name}")
        source_files.append((path, relative))

    categories = _masking_categories(run_root)
    profile_classifications = _profile_classifications(run_root)
    profile_data_types = _profile_data_types(run_root)
    omitted: list[str] = []
    sanitized: list[str] = []
    with tempfile.TemporaryDirectory(prefix="mssql_git_export_") as directory:
        staged_root = Path(directory) / "run"
        for source, relative in source_files:
            if _is_sample_payload(relative) and sample_policy == "exclude":
                omitted.append(relative.as_posix())
                continue
            destination = staged_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if _is_sample_payload(relative):
                _sanitize_sample(destination, salt=f"git-export:{database}:{run_id}", categories=categories)
                sanitized.append(relative.as_posix())

        profile_values_masked, profile_values_omitted = _sanitize_profile_values(
            staged_root,
            policy=profile_value_policy,
            salt=f"git-export-profile:{database}:{run_id}",
            classifications=profile_classifications,
            data_types=profile_data_types,
        )
        _refresh_manifest_and_checksums(
            staged_root,
            policy=sample_policy,
            omitted=omitted,
            sanitized=sanitized,
            profile_value_policy=profile_value_policy,
            profile_values_masked=profile_values_masked,
            profile_values_omitted=profile_values_omitted,
        )
        audit = audit_run_evidence(
            staged_root,
            sensitive_values=needles,
            require_git_export_policy=True,
        )
        if not audit.passed:
            raise GitExportError(f"Staged export failed the independent evidence safety audit ({len(audit.violations)} violation(s))")
        try:
            target = new_contained_path(
                git_export_root,
                ("MSSQL", database, f"run_{run_id}"),
            )
            shutil.copytree(staged_root, target)
            ensure_contained_directory(
                git_export_root,
                ("MSSQL", database, f"run_{run_id}"),
                create=False,
            )
        except UnsafeDestinationError as exc:
            raise GitExportError(str(exc)) from exc
    return target
