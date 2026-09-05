"""Load completed or partial real runs without maintaining an external registry DB."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .normalizers import read_csv_rows


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    label: str
    root: Path
    origin: str
    manifest: dict[str, Any]
    summary: dict[str, Any]

    @property
    def database(self) -> str:
        return str(self.summary.get("database") or self.manifest.get("database") or self.root.parent.name)

    @property
    def run_id(self) -> str:
        return str(self.summary.get("run_id") or self.manifest.get("run_id") or self.root.name.removeprefix("run_"))

    def csv(self, relative_path: str) -> list[dict[str, str]]:
        return read_csv_rows(self.root / relative_path)

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).is_file()

    def json(self, relative_path: str) -> Any:
        path = self.root / relative_path
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def text(self, relative_path: str) -> str | None:
        path = self.root / relative_path
        return path.read_text(encoding="utf-8-sig", errors="replace") if path.is_file() else None


def _find_manifest(root: Path) -> Path:
    candidates = (root / "00_Run_Metadata" / "manifest.json", root / "manifest.json")
    return next((path for path in candidates if path.is_file()), candidates[0])


def _derive_summary(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    stages = manifest.get("stages") or []
    errors = int(manifest.get("errors") or len(manifest.get("warnings") or []))
    statuses = [str(item.get("status") or "") for item in stages if isinstance(item, dict)]
    failed_stage_count = sum(value == "FAILED" for value in statuses)
    expected_stage_count = int(manifest.get("expected_stage_count") or (20 if stages else 0))
    if any(value == "FAILED" for value in statuses):
        status = "FAILED"
    elif expected_stage_count and len(statuses) >= expected_stage_count and all(value in {"PASS", "SKIPPED_BY_MODE"} for value in statuses):
        status = "COMPLETED_WITH_WARNINGS" if errors else "COMPLETED"
    else:
        status = "PARTIAL"
    configuration = manifest.get("configuration") or {}
    return {
        "run_id": manifest.get("run_id") or root.name.removeprefix("run_"),
        "database": manifest.get("database") or root.parent.name,
        "server_alias": configuration.get("server", "[SANITIZED]"),
        "timestamp_utc": manifest.get("timestamp_utc", ""),
        "mode": configuration.get("discovery_mode", "UNKNOWN"),
        "status": status,
        "tool_version": manifest.get("tool_version", "UNKNOWN"),
        "sql_server_version": ((manifest.get("sql_server_capabilities") or [{}])[0]).get("product_version", "UNKNOWN"),
        "sample_rows": configuration.get("profile_sample_rows", "UNKNOWN"),
        "exact_row_counts": configuration.get("profile_exact_row_counts", "UNKNOWN"),
        "mask_sensitive_data": configuration.get("profile_mask_sensitive_data", "UNKNOWN"),
        "profile_settings": {
            "sample_rows": configuration.get("profile_sample_rows", "UNKNOWN"),
            "include_sample_data": configuration.get("profile_include_sample_data", "UNKNOWN"),
            "mask_sensitive_data": configuration.get("profile_mask_sensitive_data", "UNKNOWN"),
            "exact_row_counts": configuration.get("profile_exact_row_counts", "UNKNOWN"),
            "exact_row_count_threshold": configuration.get("profile_exact_row_count_threshold", "UNKNOWN"),
            "large_table_threshold": configuration.get("profile_large_table_threshold", "UNKNOWN"),
        },
        "completed_stage_count": sum(value == "PASS" for value in statuses),
        "completion_coverage": f"{sum(value in {'PASS', 'SKIPPED_BY_MODE'} for value in statuses)}/{expected_stage_count}" if expected_stage_count else "0/0",
        "error_count": failed_stage_count,
        "warning_count": max(0, errors - failed_stage_count),
        "warning_error_count": errors,
        "legacy_derived_summary": True,
    }


def load_run(path: Path | str, *, label: str | None = None, origin: str = "output") -> RunSnapshot:
    root = Path(path).resolve()
    manifest_path = _find_manifest(root)
    if not manifest_path.is_file():
        raise ValueError(f"Run has no manifest.json: {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    summary_path = root / "00_Run_Metadata" / "run_summary.json"
    baseline = _derive_summary(root, manifest)
    summary = {**baseline, **(json.loads(summary_path.read_text(encoding="utf-8-sig")) if summary_path.is_file() else {})}
    total = int(summary.get("warning_error_count") or 0)
    summary.setdefault("error_count", baseline["error_count"])
    summary.setdefault("warning_count", max(0, total - int(summary.get("error_count") or 0)))
    summary.setdefault("coverage", summary.get("completion_coverage", "UNKNOWN"))
    summary.setdefault("profile_settings", baseline["profile_settings"])
    return RunSnapshot(label or root.name, root, origin, manifest, summary)
