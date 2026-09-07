import json
import os
from pathlib import Path
import subprocess
import tempfile

import pytest

from mssql_database_documenter.comparison import export_comparison, load_run
from mssql_database_documenter.git_export import GitExportError, create_git_export
from mssql_database_documenter.path_safety import (
    UnsafeDestinationError,
    ensure_contained_directory,
    is_reparse_point,
)
from mssql_database_documenter.report_regeneration import regenerate_reports


def _directory_link(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        completed = subprocess.run(
            ("cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)),
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if completed.returncode:
            pytest.skip(f"Windows junction creation unavailable: {completed.stderr}")
    else:
        link.symlink_to(target, target_is_directory=True)
    assert is_reparse_point(link)


def _manifested_run(output_root: Path) -> Path:
    run = output_root / "School" / "run_20260906"
    metadata = run / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    manifest = {
        "database": "School",
        "run_id": "20260906",
        "configuration": {"discovery_mode": "metadata"},
        "files": [],
    }
    (metadata / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (metadata / "run_summary.json").write_text(
        json.dumps({
            "database": "School",
            "run_id": "20260906",
            "mode": "metadata",
            "status": "COMPLETED",
        }),
        encoding="utf-8",
    )
    return run


def test_shared_guard_rejects_real_reparse_point_before_descending() -> None:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / "root"
        root.mkdir()
        outside = base / "outside"
        _directory_link(root / "nested", outside)

        with pytest.raises(UnsafeDestinationError, match="reparse point"):
            ensure_contained_directory(root, ("nested", "must-not-be-created"))

        assert list(outside.iterdir()) == []


def test_git_export_rejects_nested_reparse_destination_without_external_write() -> None:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        run = _manifested_run(base / "output")
        git_root = base / "git_export"
        outside = base / "outside"
        _directory_link(git_root / "MSSQL", outside)

        with pytest.raises(GitExportError, match="reparse point"):
            create_git_export(
                run,
                output_root=base / "output",
                git_export_root=git_root,
            )

        assert list(outside.iterdir()) == []


def test_comparison_export_rejects_nested_reparse_destination_without_external_write() -> None:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        output_root = base / "output"
        outside = base / "outside"
        _directory_link(output_root / "comparisons", outside)

        with pytest.raises(UnsafeDestinationError, match="reparse point"):
            export_comparison(
                {
                    "runs": {},
                    "warnings": [],
                    "summary": {},
                    "categories": {},
                    "semantic_note": "",
                },
                output_root,
            )

        assert list(outside.iterdir()) == []


def test_report_regeneration_rejects_nested_reparse_before_external_mkdir() -> None:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        output_root = base / "output"
        run = _manifested_run(output_root)
        regeneration_root = output_root / "report_regenerations"
        outside = base / "outside"
        _directory_link(regeneration_root / "School", outside)

        with pytest.raises(UnsafeDestinationError, match="reparse point"):
            regenerate_reports(load_run(run), output_root)

        assert list(outside.iterdir()) == []
