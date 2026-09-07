import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.profiling.sampler import (
    build_sample_plan,
    sample_failure_status,
    sanitize_sample_rows,
)
from mssql_database_documenter.profiling.sensitivity import classify_sensitivity
from mssql_database_documenter.safety import validate_read_only_sql


class SamplerTests(unittest.TestCase):
    def test_view_without_size_estimate_has_bounded_unordered_plan(self) -> None:
        plan = build_sample_plan(
            schema_name="reporting", object_name="CurrentStudents", object_type="VIEW",
            requested_rows=7, sample_tables=True, sample_views=True,
            sample_large_tables=True, estimated_rows=None, profile_large_table_threshold=10,
        )
        self.assertTrue(plan.enabled)
        self.assertEqual(plan.ordering_strategy, "UNORDERED_TOP_VIEW")
        self.assertEqual(plan.sql, "SELECT TOP (7) * FROM [reporting].[CurrentStudents]")
        validate_read_only_sql(plan.sql)

    def test_large_table_sampling_is_independent_from_profile_threshold(self) -> None:
        plan = build_sample_plan(
            schema_name="dbo", object_name="Attendance", object_type="USER_TABLE",
            requested_rows=5, sample_tables=True, sample_views=True,
            sample_large_tables=True, estimated_rows=2_000_000,
            profile_large_table_threshold=100_000,
            primary_keys=({"column_name": "AttendanceId", "key_ordinal": 1},),
        )
        self.assertTrue(plan.enabled)
        self.assertEqual(plan.ordering_strategy, "PRIMARY_KEY")
        self.assertIn("TOP (5)", plan.sql)
        self.assertIn("ORDER BY [AttendanceId]", plan.sql)
        self.assertNotIn("COUNT", plan.sql.upper())
        validate_read_only_sql(plan.sql)

    def test_only_pk_or_unique_index_is_used_for_ordering(self) -> None:
        common = dict(
            schema_name="dbo", object_name="Ledger", object_type="USER_TABLE",
            requested_rows=3, sample_tables=True, sample_views=True,
            sample_large_tables=True, estimated_rows=None, profile_large_table_threshold=100,
        )
        unordered = build_sample_plan(**common, indexes=({"index_id": 1, "index_name": "IX", "is_unique": False, "key_ordinal": 1, "column_name": "Code"},))
        unique = build_sample_plan(**common, indexes=({"index_id": 2, "index_name": "UX", "is_unique": True, "key_ordinal": 1, "column_name": "Code"},))
        self.assertEqual(unordered.ordering_strategy, "UNORDERED_TOP")
        self.assertNotIn("ORDER BY", unordered.sql)
        self.assertEqual(unique.ordering_strategy, "UNIQUE_INDEX")
        self.assertIn("ORDER BY [Code]", unique.sql)

    def test_large_table_setting_can_explicitly_disable_known_large_table(self) -> None:
        plan = build_sample_plan(
            schema_name="dbo", object_name="Archive", object_type="USER_TABLE",
            requested_rows=5, sample_tables=True, sample_views=True,
            sample_large_tables=False, estimated_rows=101, profile_large_table_threshold=100,
        )
        self.assertFalse(plan.enabled)
        self.assertEqual(plan.status, "SKIPPED_LARGE_TABLE_SAMPLING_DISABLED")
        self.assertEqual(plan.sql, "")

    def test_sample_values_are_masked_before_sampler_returns(self) -> None:
        sanitized = sanitize_sample_rows(
            ({"StudentId": 1, "StudNm": "Alice Example"},),
            column_names=("StudentId", "StudNm"),
            classify=lambda name, values: classify_sensitivity(name, values=values),
            salt="test-run",
        )
        self.assertEqual(sanitized.masked_sensitive_column_count, 1)
        self.assertEqual(sanitized.rows[0]["StudentId"], 1)
        self.assertRegex(str(sanitized.rows[0]["StudNm"]), r"^\[MASKED:[0-9a-f]{16}\]$")

    def test_failure_states_are_explicit(self) -> None:
        self.assertEqual(sample_failure_status("HYT00 query timeout"), "FAILED_TIMEOUT")
        self.assertEqual(sample_failure_status("SELECT permission denied"), "INACCESSIBLE")
        self.assertEqual(sample_failure_status("invalid object"), "FAILED_QUERY")

    def test_sampler_source_and_generated_sql_forbid_random_and_tablesample(self) -> None:
        source = (Path(__file__).parents[1] / "src" / "mssql_database_documenter" / "profiling" / "sampler.py").read_text(encoding="utf-8").upper()
        forbidden_random = "ORDER BY " + "NEWID"
        forbidden_table_sample = "TABLE" + "SAMPLE"
        self.assertNotIn(forbidden_random, source)
        self.assertNotIn(forbidden_table_sample, source)

    def test_pipeline_samples_view_and_large_table_but_masks_before_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(
                server="sql01", databases=("School",), output_root=Path(directory) / "output",
                discovery_mode="safe-profile",
                sample_row_limit=2, sample_tables=True, sample_views=True,
                sample_large_tables=True, profile_large_table_threshold=10,
                profile_mask_sensitive_data=False,
            )
            run = SequentialRun(settings, "School")
            run.data = {
                "columns": [
                    {"schema_name": "dbo", "object_name": "Student", "object_type": "USER_TABLE", "column_name": "StudentId", "column_id": 1, "data_type": "int"},
                    {"schema_name": "dbo", "object_name": "Student", "object_type": "USER_TABLE", "column_name": "StudNm", "column_id": 2, "data_type": "nvarchar"},
                    {"schema_name": "reporting", "object_name": "StudentView", "object_type": "VIEW", "column_name": "EmailAddress", "column_id": 1, "data_type": "nvarchar"},
                ],
                "table_sizes": [{"schema_name": "dbo", "object_name": "Student", "row_count": 50_000}],
                "primary_keys": [{"schema_name": "dbo", "object_name": "Student", "column_name": "StudentId", "key_ordinal": 1}],
                "indexes": [], "extended_properties": [],
            }

            def rows_for(sql: str, **_kwargs):
                if "[dbo].[Student]" in sql:
                    return [{"StudentId": 1, "StudNm": "Alice Example"}]
                if "[reporting].[StudentView]" in sql:
                    return [{"EmailAddress": "alice@example.test"}]
                raise AssertionError(sql)

            run.fetch_dynamic = MagicMock(side_effect=rows_for)
            run.prompt08_samples()
            self.assertEqual(run.fetch_dynamic.call_count, 2)
            sql_statements = [call.args[0] for call in run.fetch_dynamic.call_args_list]
            self.assertTrue(any("[reporting].[StudentView]" in sql and "ORDER BY" not in sql for sql in sql_statements))
            self.assertTrue(any("[dbo].[Student]" in sql and "ORDER BY [StudentId]" in sql for sql in sql_statements))

            with run.artifact("SAMPLE_INDEX.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                index = {row["object_name"]: row for row in csv.DictReader(handle)}
            self.assertEqual(index["Student"]["object_type"], "USER_TABLE")
            self.assertEqual(index["Student"]["requested_rows"], "2")
            self.assertEqual(index["Student"]["returned_rows"], "1")
            self.assertEqual(index["Student"]["status"], "SAMPLED")
            self.assertEqual(index["Student"]["masked_sensitive_column_count"], "1")
            self.assertEqual(index["StudentView"]["status"], "SAMPLED")
            payload = "\n".join(path.read_text(encoding="utf-8-sig") for path in (run.root / "14_Samples").glob("*.csv"))
            self.assertNotIn("Alice Example", payload)
            self.assertNotIn("alice@example.test", payload)

    def test_view_timeout_is_recorded_in_sample_index_without_stopping_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(
                    server="sql01", databases=("School",), output_root=Path(directory) / "output",
                    discovery_mode="safe-profile", sample_row_limit=2, sample_views=True,
                ),
                "School",
            )
            run.data = {
                "columns": [{"schema_name": "reporting", "object_name": "SlowView", "object_type": "VIEW", "column_name": "StudNm", "column_id": 1, "data_type": "nvarchar"}],
                "table_sizes": [], "primary_keys": [], "indexes": [], "extended_properties": [],
            }
            run.fetch_dynamic = MagicMock(side_effect=RuntimeError("HYT00 query timeout"))
            run.prompt08_samples()
            with run.artifact("SAMPLE_INDEX.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["status"], "FAILED_TIMEOUT")
            self.assertEqual(row["returned_rows"], "0")
            self.assertEqual(row["object_type"], "VIEW")

    def test_large_table_remains_excluded_from_deep_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(
                    server="sql01", databases=("School",), output_root=Path(directory) / "output",
                    discovery_mode="safe-profile", profile_large_table_threshold=10,
                    sample_large_tables=True,
                ),
                "School",
            )
            run.data = {
                "columns": [{"schema_name": "dbo", "object_name": "Large", "column_name": "Value", "data_type": "int", "object_type": "USER_TABLE", "is_computed": False, "column_id": 1}],
                "table_sizes": [{"schema_name": "dbo", "object_name": "Large", "row_count": 11}],
                "extended_properties": [],
            }
            run.fetch_dynamic = MagicMock()
            run.prompt07_profile()
            self.assertEqual(run.data["column_profile"][0]["profile_status"], "SKIPPED_FOR_SAFETY_LARGE_TABLE")
            run.fetch_dynamic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
