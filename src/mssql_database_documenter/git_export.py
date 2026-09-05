"""Explicit, sanitized Git-export creation for an existing real run."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Iterable

from .inventory import safe_path_component
from .evidence_safety import audit_run_evidence
from .redaction import redact_text


class GitExportError(ValueError):
    pass


ALLOWED_EVIDENCE_SUFFIXES = frozenset({".csv", ".html", ".json", ".md", ".mmd", ".sha256", ".sql", ".txt"})
FORBIDDEN_TRANSIENT_PARTS = frozenset({"__pycache__", ".pytest_cache", "cache", "logs", "temp", "tmp"})


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def create_git_export(
    run_root: Path,
    *,
    output_root: Path,
    git_export_root: Path,
    sensitive_values: Iterable[str] = (),
) -> Path:
    """Copy one completed/partial run only after an explicit user action."""
    run_root = run_root.resolve()
    if not _contained(output_root, run_root) or not run_root.is_dir():
        raise GitExportError("Selected run is outside the configured output root")
    manifest_path = run_root / "00_Run_Metadata" / "manifest.json"
    if not manifest_path.is_file():
        raise GitExportError("Selected directory is not a real manifested run")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    database = safe_path_component(str(manifest.get("database") or run_root.parent.name))
    run_id = safe_path_component(str(manifest.get("run_id") or run_root.name.removeprefix("run_")))
    target = git_export_root / "MSSQL" / database / f"run_{run_id}"
    if target.exists():
        raise GitExportError("A Git export already exists for this run")

    audit = audit_run_evidence(run_root, sensitive_values=sensitive_values)
    if not audit.passed:
        raise GitExportError(f"Run failed the independent evidence safety audit ({len(audit.violations)} violation(s))")

    forbidden = {".env", ".env.local", "credentials.json"}
    needles = [str(value) for value in sensitive_values if value and len(str(value)) >= 3]
    for path in run_root.rglob("*"):
        relative = path.relative_to(run_root)
        if path.is_symlink():
            raise GitExportError(f"Run contains a symbolic link: {relative.as_posix()}")
        if any(part.casefold() in FORBIDDEN_TRANSIENT_PARTS for part in relative.parts):
            raise GitExportError(f"Run contains a transient/internal path: {relative.as_posix()}")
        if not path.is_file():
            continue
        if path.name.casefold() in forbidden:
            raise GitExportError("Run contains a forbidden credential file")
        if path.suffix.casefold() not in ALLOWED_EVIDENCE_SUFFIXES:
            raise GitExportError(f"Run contains a non-evidence file type: {path.name}")
        if path.suffix.casefold() in ALLOWED_EVIDENCE_SUFFIXES:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            if any(value.casefold() in text.casefold() for value in needles):
                raise GitExportError(f"Configured sensitive value found in {path.name}")
            if redact_text(text, sensitive_values=tuple(needles)) != text:
                raise GitExportError(f"Potential unredacted secret assignment found in {path.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(run_root, target)
    return target
