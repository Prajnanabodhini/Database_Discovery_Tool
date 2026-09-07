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
from .profiling.sensitivity import mask_value
from .redaction import redact_text


class GitExportError(ValueError):
    pass


ALLOWED_EVIDENCE_SUFFIXES = frozenset({".csv", ".html", ".json", ".md", ".mmd", ".sha256", ".sql", ".txt"})
FORBIDDEN_TRANSIENT_PARTS = frozenset({"__pycache__", ".pytest_cache", "cache", "logs", "temp", "tmp"})
VALID_SAMPLE_POLICIES = frozenset({"exclude", "masked_only"})
SAMPLE_CONTROL_FILES = frozenset({"masking_report.csv", "sample_index.csv"})


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
) -> Path:
    """Build and audit an isolated export; publish it only after every gate passes."""
    run_root = run_root.resolve()
    sample_policy = sample_policy.strip().casefold()
    if sample_policy not in VALID_SAMPLE_POLICIES:
        raise GitExportError("Git export sample policy must be exclude or masked_only; raw is never allowed")
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

        _refresh_manifest_and_checksums(staged_root, policy=sample_policy, omitted=omitted, sanitized=sanitized)
        audit = audit_run_evidence(staged_root, sensitive_values=needles)
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
