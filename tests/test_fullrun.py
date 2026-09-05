import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

from mssql_database_documenter.contracts import DISCOVERY_CAPABILITY_MATRIX, EVIDENCE_CLASSES, EXTRA_OUTPUTS, REQUIRED_OUTPUTS
from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import DiscoveryCancelled, SequentialRun, _classification, _definition_references, _is_access_limitation, _known_row_estimate, _mask, _qid, _static_column_references, _type_family, _within_safety_threshold, run_all
from mssql_database_documenter.programmable_queries import PROGRAMMABLE_QUERIES, SQL_AGENT_QUERY
from mssql_database_documenter.queries import METADATA_QUERIES, QUERIES
from mssql_database_documenter.safety import validate_read_only_sql


class FullRunTests(unittest.TestCase):
    def test_expected_domain_packages_are_importable(self) -> None:
        for package in ("metadata", "profiling", "relationships", "lineage", "analysis", "reporting", "comparison", "web"):
            with self.subTest(package=package):
                __import__(f"mssql_database_documenter.{package}")

    def test_every_static_query_passes_fail_closed_gate(self) -> None:
        for query in QUERIES + METADATA_QUERIES + PROGRAMMABLE_QUERIES + (SQL_AGENT_QUERY,):
            with self.subTest(query=query.name):
                validate_read_only_sql(query.sql)

    def test_comprehensive_discovery_capability_matrix_is_backed_by_artifacts(self) -> None:
        expected = {"server_database_metadata", "schemas", "tables_columns", "keys_relationships", "constraints_indexes", "storage_rows_shapes", "profiles_samples", "programmable_objects", "synonyms_sequences", "computed_columns_extended_properties", "agent_jobs", "dependencies_lineage", "pipelines_external_references", "cardinality_orphans", "quality_classification_duplicates", "high_connectivity", "manifests_checksums_errors"}
        self.assertEqual(set(DISCOVERY_CAPABILITY_MATRIX), expected)
        artifacts = set(REQUIRED_OUTPUTS) | set(EXTRA_OUTPUTS)
        for capability, names in DISCOVERY_CAPABILITY_MATRIX.items():
            with self.subTest(capability=capability):
                self.assertTrue(set(names).issubset(artifacts))
        metadata_names = {query.name for query in METADATA_QUERIES}
        self.assertTrue({"schemas", "tables", "columns", "primary_keys", "foreign_keys", "indexes", "constraints", "extended_properties", "table_sizes"}.issubset(metadata_names))
        programmable_names = {query.name for query in PROGRAMMABLE_QUERIES}
        self.assertTrue({"views", "procedures", "functions", "triggers", "synonyms", "sequences", "parameters", "dependencies"}.issubset(programmable_names))
        columns_query = next(query for query in METADATA_QUERIES if query.name == "columns")
        self.assertIn("computed_definition", columns_query.columns)
        self.assertEqual(SQL_AGENT_QUERY.name, "sql_agent_jobs")

    def test_evidence_classes_are_disjoint_and_explicit(self) -> None:
        self.assertEqual(EVIDENCE_CLASSES, {"FACT", "DATA_VALIDATION", "INFERENCE", "UNKNOWN"})

    def test_required_output_contract_has_unique_paths(self) -> None:
        paths = [f"{folder}/{name}" for name, folder in REQUIRED_OUTPUTS.items()]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertGreaterEqual(len(paths), 45)

    def test_identifier_quoting_is_bracket_safe(self) -> None:
        self.assertEqual(_qid("a]b"), "[a]]b]")

    def test_credentials_are_always_redacted(self) -> None:
        category, action = _classification("PasswordHash")
        self.assertEqual((category, action), ("Credential", "REDACT"))
        self.assertEqual(_mask("secret", category, "salt"), "[REDACTED]")

    def test_pseudonymization_is_deterministic_within_run(self) -> None:
        first = _mask("person@example.test", "PII", "run-salt")
        second = _mask("person@example.test", "PII", "run-salt")
        self.assertEqual(first, second)
        self.assertNotIn("person", str(first))

    def test_credentials_remain_redacted_when_general_masking_is_disabled(self) -> None:
        self.assertEqual(_mask("secret", "Credential", "salt", False), "[REDACTED]")
        self.assertEqual(_mask("ordinary", "Unknown", "salt", False), "ordinary")

    def test_column_profile_masks_sensitive_extrema_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(
                server="sql01", databases=("School",), output_root=Path(directory) / "output",
                profile_distinct_values=False, profile_mask_sensitive_data=True,
            )
            run = SequentialRun(settings, "School")
            run.data = {
                "columns": [{"schema_name": "dbo", "object_name": "Person", "column_name": "EmailAddress", "data_type": "nvarchar", "object_type": "USER_TABLE", "is_computed": False, "column_id": 1}],
                "table_sizes": [{"schema_name": "dbo", "object_name": "Person", "row_count": 1}],
                "extended_properties": [],
            }
            run.fetch_dynamic = MagicMock(return_value=[{"total_rows": 1, "non_null_count": 1, "distinct_count": None, "minimum_value": "person@example.test", "maximum_value": "person@example.test", "empty_string_count": 0, "whitespace_string_count": 0, "minimum_length": 19, "maximum_length": 19}])
            run.prompt07_profile()
            row = run.data["column_profile"][0]
            self.assertEqual(row["sensitivity_category"], "PII")
            self.assertRegex(row["minimum_value"], r"^\[MASKED:[0-9a-f]{16}\]$")
            self.assertRegex(row["maximum_value"], r"^\[MASKED:[0-9a-f]{16}\]$")
            self.assertNotIn("person@example.test", (run.artifact("COLUMN_PROFILE.csv")).read_text(encoding="utf-8-sig"))

    def test_only_known_inaccessibility_errors_can_continue(self) -> None:
        self.assertTrue(_is_access_limitation(Exception("Could not use view because of binding errors")))
        self.assertTrue(_is_access_limitation(Exception("SELECT permission denied")))
        self.assertFalse(_is_access_limitation(Exception("Invalid column name in project query")))

    def test_dependency_query_uses_catalog_join_for_target_column(self) -> None:
        query = next(item for item in PROGRAMMABLE_QUERIES if item.name == "dependencies")
        self.assertNotIn("referenced_minor_name", query.sql)
        self.assertIn("sys.columns", query.sql)

    def test_static_reference_analysis_separates_reads_writes_and_calls(self) -> None:
        row = {"definition_sanitized": "SELECT * FROM dbo.Source; INSERT INTO audit.Target(id) SELECT id FROM dbo.Source; EXEC dbo.NextStep"}
        references = _definition_references(row)
        operations = {(item["operation"], item["target_schema"], item["target_object"]) for item in references}
        self.assertIn(("READ", "dbo", "Source"), operations)
        self.assertIn(("WRITE", "audit", "Target"), operations)
        self.assertIn(("CALL", "dbo", "NextStep"), operations)

    def test_type_families_are_stable(self) -> None:
        self.assertEqual(_type_family("nvarchar"), "STRING")
        self.assertEqual(_type_family("decimal"), "NUMERIC")
        self.assertEqual(_type_family("datetime2"), "DATE_TIME")

    def test_scan_threshold_fails_closed_when_row_estimate_is_unavailable(self) -> None:
        sizes = {
            "dbo.Small": {"row_count": 100},
            "dbo.Large": {"row_count": 100_001},
            "dbo.EmptyValue": {"row_count": ""},
            "dbo.Invalid": {"row_count": "unknown"},
        }
        self.assertEqual(_known_row_estimate(sizes, "dbo.Small"), 100)
        self.assertTrue(_within_safety_threshold(sizes, "dbo.Small", 100_000))
        for key in ("dbo.Large", "dbo.EmptyValue", "dbo.Invalid", "dbo.Missing"):
            with self.subTest(key=key):
                self.assertFalse(_within_safety_threshold(sizes, key, 100_000))

    def test_fullrun_has_no_expensive_random_sampling_sort(self) -> None:
        source = Path(__file__).parents[1] / "src" / "mssql_database_documenter" / "fullrun.py"
        text = source.read_text(encoding="utf-8").upper()
        self.assertNotIn("ORDER BY NEWID", text)
        self.assertNotIn("TABLESAMPLE", text)

    def test_static_alias_column_lineage_is_attempted(self) -> None:
        row = {"definition_sanitized": "SELECT s.id, SUM(s.amount) AS total FROM dbo.Source AS s GROUP BY s.id"}
        references = _static_column_references(row, {("dbo", "Source"): {"id", "amount"}})
        classifications = {(item["target_column"], item["lineage_type"]) for item in references}
        self.assertIn(("id", "DIRECT"), classifications)
        self.assertIn(("amount", "AGGREGATED"), classifications)

    def test_cancelled_real_attempt_gets_truthful_partial_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(server="sql01", databases=("School",), output_root=Path(directory) / "output"),
                "School",
                cancel_requested=lambda: True,
            )
            with self.assertRaises(DiscoveryCancelled):
                run.run()
            self.assertTrue(run.root.is_dir())
            summary = json.loads((run.root / "00_Run_Metadata" / "run_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "CANCELLED")
            self.assertTrue((run.root / "00_Run_Metadata" / "manifest.json").is_file())

    def test_multi_database_runner_is_strictly_sequential_in_configured_order(self) -> None:
        settings = Settings(server="sql01", databases=("First", "Second"))
        first = MagicMock()
        second = MagicMock()
        first.run.return_value = Path("first-run")
        second.run.return_value = Path("second-run")
        with patch("mssql_database_documenter.fullrun.SequentialRun", side_effect=[first, second]) as sequential:
            self.assertEqual(run_all(settings), [Path("first-run"), Path("second-run")])
        self.assertEqual([item.args[1] for item in sequential.call_args_list], ["First", "Second"])
        first.run.assert_called_once_with()
        second.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
