import json
import os
from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.git_export import GitExportError, create_git_export
from mssql_database_documenter.web.file_browser import FileBrowser, PathSecurityError


def manifested_run(output: Path, database: str = "School", run_id: str = "20260101_000000") -> Path:
    root = output / database / f"run_{run_id}"
    metadata = root / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    summary = {"run_id": run_id, "database": database, "mode": "metadata", "status": "COMPLETED", "tool_version": "0.3.0", "timestamp_utc": "2026-01-01T00:00:00Z", "server_alias": "[SANITIZED]", "sql_server_version": "16", "sample_rows": 0, "exact_row_counts": False, "completed_stage_count": 20, "warning_error_count": 0}
    (metadata / "manifest.json").write_text(json.dumps({"run_id": run_id, "database": database, "configuration": {"discovery_mode": "metadata"}, "stages": []}), encoding="utf-8")
    (metadata / "run_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (root / "99_Git_Handoff").mkdir()
    (root / "99_Git_Handoff" / "SAFE_TO_COMMIT_CHECKLIST.md").write_text("# Safe\n\n- PASS", encoding="utf-8")
    return root


class FileBrowserTests(unittest.TestCase):
    def test_missing_roots_are_reported_without_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            browser = FileBrowser(base / "output", base / "git_export")
            self.assertFalse(browser.list_directory("output")["exists"])
            self.assertEqual(browser.list_directory("git_export")["message"], "No Git exports generated yet.")
            self.assertFalse((base / "output").exists())
            self.assertFalse((base / "git_export").exists())

    def test_traversal_absolute_and_unknown_roots_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "output").mkdir()
            browser = FileBrowser(base / "output", base / "git_export")
            for value in ("../secret", "a/../../secret", str((base / "elsewhere").resolve())):
                with self.subTest(value=value), self.assertRaises(PathSecurityError):
                    browser.resolve("output", value, must_exist=False)
            with self.assertRaises(PathSecurityError):
                browser.resolve("unknown", "")

    def test_symlink_escape_is_blocked_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            outside = base / "outside"
            output.mkdir()
            outside.mkdir()
            link = output / "escape"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation is not available to this Windows identity")
            with self.assertRaises(PathSecurityError):
                FileBrowser(output, base / "git_export").resolve("output", "escape")
            listing = FileBrowser(output, base / "git_export").list_directory("output")
            self.assertNotIn("escape", {entry["name"] for entry in listing["entries"]})

    def test_registry_and_explicit_git_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            git_root = base / "git_export"
            run = manifested_run(output)
            browser = FileBrowser(output, git_root)
            listing = browser.list_directory("output", run.relative_to(output).as_posix())
            self.assertEqual(listing["database"], "School")
            self.assertEqual(listing["run"], "run_20260101_000000")
            self.assertTrue(all("modified_utc" in entry and "type" in entry for entry in listing["entries"]))
            records = browser.scan_runs()
            self.assertEqual(records[0]["database"], "School")
            required = {"run_id", "database", "server_alias", "timestamp_utc", "mode", "status", "tool_version", "sql_server_version", "profile_settings", "coverage", "error_count", "warning_count", "path"}
            self.assertTrue(required.issubset(records[0]))
            self.assertFalse(git_root.exists())
            exported = create_git_export(run, output_root=output, git_export_root=git_root)
            self.assertTrue(exported.is_dir())
            records = browser.scan_runs()
            self.assertEqual({item["root"] for item in records}, {"output", "git_export"})
            self.assertTrue(next(item for item in records if item["root"] == "git_export")["sanitized"])

    def test_partial_manifest_is_indexed_without_mutable_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            run = manifested_run(output, run_id="partial")
            (run / "00_Run_Metadata" / "run_summary.json").unlink()
            manifest = {"run_id": "partial", "database": "School", "timestamp_utc": "2026-01-02T00:00:00Z", "tool_version": "0.3.0", "configuration": {"server": "[SANITIZED]", "discovery_mode": "safe-profile", "profile_sample_rows": 12, "profile_mask_sensitive_data": True}, "stages": [{"prompt": "02", "status": "PASS"}], "errors": 2, "warnings": ["limited", "skipped"]}
            (run / "00_Run_Metadata" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            record = FileBrowser(output, base / "git").scan_runs()[0]
            self.assertEqual(record["status"], "PARTIAL")
            self.assertEqual(record["coverage"], "1/20")
            self.assertEqual(record["error_count"], 0)
            self.assertEqual(record["warning_count"], 2)
            self.assertEqual(record["profile_settings"]["sample_rows"], 12)

    def test_git_export_rejects_non_evidence_and_transient_files_before_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = manifested_run(base / "output")
            (run / "payload.bin").write_bytes(b"not approved evidence")
            git_root = base / "git_export"
            with self.assertRaises(GitExportError):
                create_git_export(run, output_root=base / "output", git_export_root=git_root)
            self.assertFalse(git_root.exists())

    def test_git_export_rejects_symlinks_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = manifested_run(base / "output")
            outside = base / "outside.txt"
            outside.write_text("external", encoding="utf-8")
            try:
                os.symlink(outside, run / "linked.txt")
            except OSError:
                self.skipTest("Symlink creation is not available to this Windows identity")
            git_root = base / "git_export"
            with self.assertRaises(GitExportError):
                create_git_export(run, output_root=base / "output", git_export_root=git_root)
            self.assertFalse(git_root.exists())


if __name__ == "__main__":
    unittest.main()
