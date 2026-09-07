import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.inventory import (
    OUTPUT_FOLDERS, _new_run_directory, _write_manifest_and_checksums,
    run_inventory, safe_path_component,
)
from mssql_database_documenter.queries import METADATA_QUERIES
from mssql_database_documenter.safety import validate_read_only_sql


class InventoryTests(unittest.TestCase):
    def test_runtime_output_folder_contract_is_complete(self) -> None:
        self.assertEqual(OUTPUT_FOLDERS, (
            "00_Run_Metadata", "01_Executive_Summary", "02_Server_Database", "03_Schemas",
            "04_Tables", "05_Columns", "06_Keys_Relationships", "07_Indexes_Constraints",
            "08_Views", "09_Stored_Procedures", "10_Functions", "11_Triggers",
            "12_Synonyms_Sequences", "13_Data_Profiling", "14_Samples", "15_Lineage",
            "16_Pipelines", "17_Data_Quality", "18_Risks_Uncertainties", "19_Diagrams",
            "20_Object_Documentation", "21_HTML_Report", "99_Git_Handoff",
        ))

    def test_all_metadata_queries_pass_safety_gate(self) -> None:
        for query in METADATA_QUERIES:
            with self.subTest(query=query.name):
                validate_read_only_sql(query.sql)
                self.assertTrue(query.columns)
                self.assertTrue(query.output_folder)
                self.assertTrue(query.output_name.endswith(".csv"))

    def test_database_path_component_cannot_escape_output(self) -> None:
        self.assertEqual(safe_path_component(r"..\outside/name"), "_outside_name")

    def test_new_run_reserves_only_root_and_stages_create_needed_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _, run_directory = _new_run_directory(Path(temp_dir), "Database")
            created = {item.name for item in run_directory.iterdir() if item.is_dir()}
            self.assertEqual(created, set())
            run = SequentialRun(Settings(output_root=Path(temp_dir) / "other"), "Database")
            run.prompt02_safety()
            created = {item.name for item in run.root.iterdir() if item.is_dir()}
            self.assertEqual(created, {"00_Run_Metadata"})

    def test_inventory_manifest_truthfully_resolves_metadata_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_id, run_directory = _new_run_directory(Path(temp_dir), "School")
            _write_manifest_and_checksums(
                run_directory, run_id, "School",
                Settings(discovery_mode="full-readonly"), [],
            )
            manifest = json.loads((run_directory / "00_Run_Metadata" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["configuration"]["requested_discovery_mode"], "full-readonly")
            self.assertEqual(manifest["configuration"]["discovery_mode"], "metadata")
            self.assertEqual(manifest["resolved_mode_policy"]["mode"], "metadata")
            self.assertFalse(manifest["resolved_mode_policy"]["permits_data_scans"])

    def test_initial_connection_failure_retains_sanitized_manifested_failed_run(self) -> None:
        secret_values = ("private-sql", "reader-user", "reader-password")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir) / "output"
            preexisting = output_root / "School" / "preexisting"
            preexisting.mkdir(parents=True)
            marker = preexisting / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")
            before_marker = hashlib.sha256(marker.read_bytes()).hexdigest()
            settings = Settings(
                server=secret_values[0], databases=("School",),
                trusted_connection=False, username=secret_values[1], password=secret_values[2],
                output_root=output_root,
            )
            failure = RuntimeError(
                f"Login failed at {secret_values[0]} for {secret_values[1]} using {secret_values[2]}"
            )

            def fail_connection(*_args, **_kwargs):
                reserved = list((output_root / "School").glob("run_*"))
                self.assertEqual(len(reserved), 1)
                initial_manifest = json.loads(reserved[0].joinpath(
                    "00_Run_Metadata", "manifest.json",
                ).read_text(encoding="utf-8"))
                self.assertEqual(initial_manifest["status"], "INITIALIZING")
                self.assertEqual(initial_manifest["completed_stages"], [])
                raise failure

            with (
                patch("mssql_database_documenter.inventory.connect", side_effect=fail_connection),
                patch("mssql_database_documenter.inventory._fetch") as fetch,
                self.assertRaises(RuntimeError) as raised,
            ):
                run_inventory(settings, "School")

            fetch.assert_not_called()
            for secret in secret_values:
                self.assertNotIn(secret, str(raised.exception))
            self.assertEqual(hashlib.sha256(marker.read_bytes()).hexdigest(), before_marker)
            runs = list((output_root / "School").glob("run_*"))
            self.assertEqual(len(runs), 1)
            run = runs[0]
            run.resolve().relative_to(output_root.resolve())
            metadata = run / "00_Run_Metadata"
            for name in (
                "manifest.json", "run_summary.json", "RUN_CONFIGURATION.json",
                "STAGE_STATUS.json", "DISCOVERY_ERRORS.csv", "checksums.sha256",
            ):
                self.assertTrue((metadata / name).is_file(), name)
            summary = json.loads((metadata / "run_summary.json").read_text(encoding="utf-8"))
            manifest = json.loads((metadata / "manifest.json").read_text(encoding="utf-8"))
            stages = json.loads((metadata / "STAGE_STATUS.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["completed_stage_count"], 0)
            self.assertEqual(summary["error_count"], 1)
            self.assertEqual(manifest["status"], "FAILED")
            self.assertEqual(manifest["completed_stages"], [])
            self.assertEqual(stages[0]["status"], "FAILED")
            self.assertEqual(stages[1]["status"], "NOT_STARTED")
            combined = "\n".join(
                path.read_text(encoding="utf-8-sig", errors="replace")
                for path in run.rglob("*") if path.is_file()
            )
            for secret in secret_values:
                self.assertNotIn(secret, combined)
            for line in (metadata / "checksums.sha256").read_text(encoding="utf-8").splitlines():
                digest, relative = line.split("  ", 1)
                self.assertEqual(digest, hashlib.sha256((run / relative).read_bytes()).hexdigest())

    def test_successful_inventory_retains_completed_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir) / "output"
            settings = Settings(server="sql01", databases=("School",), output_root=output_root)
            connection = MagicMock()
            with patch("mssql_database_documenter.inventory.connect") as connect_mock, patch(
                "mssql_database_documenter.inventory._fetch", return_value=[],
            ):
                connect_mock.return_value.__enter__.return_value = connection
                result = run_inventory(settings, "School")
            summary = json.loads(result.run_directory.joinpath(
                "00_Run_Metadata", "run_summary.json",
            ).read_text(encoding="utf-8"))
            manifest = json.loads(result.run_directory.joinpath(
                "00_Run_Metadata", "manifest.json",
            ).read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "COMPLETED")
            self.assertEqual(summary["completion_coverage"], "2/2")
            self.assertEqual(manifest["completed_stages"], ["connection", "metadata"])
            self.assertEqual(result.query_count, len(METADATA_QUERIES))
            self.assertEqual(result.error_count, 0)

    def test_query_failure_remains_warning_with_header_only_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                server="sql01", databases=("School",),
                output_root=Path(temp_dir) / "output",
            )
            failed_query = METADATA_QUERIES[0]

            def fetch(_cursor, query):
                if query.name == failed_query.name:
                    raise PermissionError("SELECT permission denied")
                return []

            with patch("mssql_database_documenter.inventory.connect") as connect_mock, patch(
                "mssql_database_documenter.inventory._fetch", side_effect=fetch,
            ):
                connect_mock.return_value.__enter__.return_value = MagicMock()
                result = run_inventory(settings, "School")
            summary = json.loads(result.run_directory.joinpath(
                "00_Run_Metadata", "run_summary.json",
            ).read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "COMPLETED_WITH_WARNINGS")
            self.assertEqual(summary["error_count"], 0)
            self.assertEqual(summary["warning_count"], 1)
            with result.run_directory.joinpath(
                failed_query.output_folder, failed_query.output_name,
            ).open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                self.assertEqual(tuple(next(reader)), failed_query.columns)
                self.assertEqual(list(reader), [])


if __name__ == "__main__":
    unittest.main()
