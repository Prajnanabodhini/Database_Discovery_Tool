import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mssql_database_documenter.comparison import load_run
from mssql_database_documenter.report_regeneration import regenerate_reports
from mssql_database_documenter.web.renderers import render_file


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _manifested_run(output_root: Path, secret: str) -> Path:
    run = output_root / "School" / "run_20260906_120000"
    metadata = run / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    manifest = {
        "run_id": "20260906_120000", "database": "School", "tool_version": "0.3.0",
        "timestamp_utc": "2026-09-06T12:00:00+00:00",
        "configuration": {"server": "[SANITIZED]", "discovery_mode": "metadata+logic"},
        "stages": [{"prompt": "02", "status": "PASS"}],
        "warnings": [f"password={secret}"], "errors": 1,
    }
    (metadata / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (metadata / "run_summary.json").write_text(json.dumps({"run_id": "20260906_120000", "database": "School", "mode": "metadata+logic", "status": "COMPLETED_WITH_WARNINGS", "warning_error_count": 1}), encoding="utf-8")
    (metadata / "DISCOVERY_COVERAGE.md").write_text("# Coverage\n\nOne warning requires review.\n", encoding="utf-8")
    summary = run / "01_Executive_Summary" / "MSSQL_EXECUTIVE_SUMMARY.md"
    summary.parent.mkdir()
    summary.write_text("# School database\n\nCanonical executive summary.\n", encoding="utf-8")
    catalogue = run / "04_Tables" / "TABLE_CATALOGUE.csv"
    catalogue.parent.mkdir()
    with catalogue.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("schema_name", "object_name"))
        writer.writeheader()
        writer.writerows(({"schema_name": "dbo", "object_name": "Student"}, {"schema_name": "dbo", "object_name": "Class"}))
    return run


class ReportRegenerationTests(unittest.TestCase):
    def test_regeneration_is_versioned_offline_and_preserves_canonical_source(self) -> None:
        secret = "prompt11-fake-secret"
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "output"
            source = _manifested_run(output_root, secret)
            before = _hashes(source)
            snapshot = load_run(source)
            with patch("mssql_database_documenter.connection.connect", side_effect=AssertionError("database connection attempted")) as connect:
                first = regenerate_reports(snapshot, output_root, sensitive_values=(secret,))
                second = regenerate_reports(snapshot, output_root, sensitive_values=(secret,))

            connect.assert_not_called()
            self.assertEqual(_hashes(source), before)
            self.assertNotEqual(first["destination"], second["destination"])
            self.assertNotIn(source, first["destination"].parents)
            self.assertTrue(first["destination"].name.startswith("regen_"))
            for name in ("html", "markdown", "manifest", "checksums"):
                self.assertTrue(first[name].is_file(), name)
            manifest = json.loads(first["manifest"].read_text(encoding="utf-8"))
            self.assertFalse(manifest["database_connection_attempted"])
            self.assertFalse(manifest["canonical_source_mutated"])
            self.assertEqual(manifest["source_file_count"], len(before))
            combined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in first["destination"].rglob("*") if path.is_file())
            self.assertNotIn(secret, combined)
            self.assertIn("[REDACTED]", combined)

    def test_regenerated_html_is_useful_in_safe_browser_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "output"
            source = _manifested_run(output_root, "not-present")
            result = regenerate_reports(load_run(source), output_root)
            html_source = result["html"].read_text(encoding="utf-8")
            self.assertNotIn("<script", html_source.casefold())
            for text in ("Regenerated report", "School", "metadata+logic", "Canonical executive summary", "TABLE_CATALOGUE.csv", "2"):
                self.assertIn(text, html_source)
            rendered = render_file(result["html"])
            self.assertEqual(rendered["kind"], "html")
            self.assertTrue(rendered["trusted"])
            self.assertIn("Regenerated report", rendered["html"])
            self.assertIn("Canonical executive summary", rendered["html"])


if __name__ == "__main__":
    unittest.main()
