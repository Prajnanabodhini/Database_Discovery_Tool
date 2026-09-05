from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.inventory import OUTPUT_FOLDERS, _new_run_directory, safe_path_component
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


if __name__ == "__main__":
    unittest.main()
