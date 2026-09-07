import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.profiling.sampler import (
    VIEW_SAMPLE_ALLOWED_STATUS,
    VIEW_SAMPLE_DENIED_STATUS,
    build_sample_plan,
    evaluate_view_sample_eligibility,
    sample_failure_status,
    sanitize_sample_rows,
)
from mssql_database_documenter.profiling.sensitivity import classify_sensitivity
from mssql_database_documenter.safety import validate_read_only_sql


class SamplerTests(unittest.TestCase):
    @staticmethod
    def eligibility(
        *,
        definition: str = "CREATE VIEW [reporting].[CurrentStudents] AS SELECT * FROM [dbo].[Student]",
        view_updates: dict[str, object] | None = None,
        dependencies=(),
        static_references=(),
        synonyms=(),
        dependency_discovery_complete: bool = True,
    ):
        view = {
            "schema_name": "reporting",
            "object_name": "CurrentStudents",
            "definition_available": True,
            "definition_sanitized": definition,
            "dynamic_sql_present": False,
        }
        view.update(view_updates or {})
        return evaluate_view_sample_eligibility(
            current_database="School",
            schema_name="reporting",
            object_name="CurrentStudents",
            view=view,
            dependencies=dependencies,
            static_references=static_references,
            synonyms=synonyms,
            dependency_discovery_complete=dependency_discovery_complete,
        )

    def test_view_without_size_estimate_has_bounded_unordered_plan(self) -> None:
        eligibility = self.eligibility(
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_schema": "dbo", "target_object": "Student", "referenced_id": 42,
            },),
        )
        plan = build_sample_plan(
            schema_name="reporting", object_name="CurrentStudents", object_type="VIEW",
            requested_rows=7, sample_tables=True, sample_views=True,
            sample_large_tables=True, estimated_rows=None, profile_large_table_threshold=10,
            view_eligibility=eligibility,
        )
        self.assertTrue(plan.enabled)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_ALLOWED_STATUS)
        self.assertEqual(plan.ordering_strategy, "UNORDERED_TOP_VIEW")
        self.assertEqual(plan.sql, "SELECT TOP (7) * FROM [reporting].[CurrentStudents]")
        validate_read_only_sql(plan.sql)

    def test_view_plan_without_eligibility_evidence_fails_closed(self) -> None:
        plan = build_sample_plan(
            schema_name="reporting", object_name="CurrentStudents",
            object_type="VIEW", requested_rows=7,
            sample_tables=True, sample_views=True, sample_large_tables=True,
            estimated_rows=None, profile_large_table_threshold=10,
        )
        self.assertFalse(plan.enabled)
        self.assertEqual(plan.status, VIEW_SAMPLE_DENIED_STATUS)
        self.assertEqual(plan.sql, "")
        self.assertIn("VIEW_ELIGIBILITY_EVIDENCE_NOT_PROVIDED", plan.eligibility_reason)

    def test_local_only_view_is_sample_eligible(self) -> None:
        eligibility = self.eligibility(
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_schema": "dbo", "target_object": "Student", "referenced_id": 42,
            },),
        )
        self.assertTrue(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_ALLOWED_STATUS)
        self.assertEqual(eligibility.reasons, ())

    def test_current_database_three_part_view_reference_is_allowed(self) -> None:
        eligibility = self.eligibility(
            definition="CREATE VIEW reporting.CurrentStudents AS SELECT * FROM School.dbo.Student",
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_database": "School", "target_schema": "dbo",
                "target_object": "Student", "referenced_id": "",
            },),
        )
        self.assertTrue(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_ALLOWED_STATUS)

    def test_other_database_view_reference_is_denied(self) -> None:
        eligibility = self.eligibility(
            definition="CREATE VIEW reporting.CurrentStudents AS SELECT * FROM OtherDb.dbo.Student",
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_database": "OtherDb", "target_schema": "dbo",
                "target_object": "Student", "referenced_id": "",
            },),
        )
        self.assertFalse(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_DENIED_STATUS)
        self.assertIn("CROSS_DATABASE_DEPENDENCY", eligibility.reasons)

    def test_linked_server_view_reference_is_denied(self) -> None:
        eligibility = self.eligibility(
            definition="CREATE VIEW reporting.CurrentStudents AS SELECT * FROM LinkedSrv.OtherDb.dbo.Student",
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_server": "LinkedSrv", "target_database": "OtherDb",
                "target_schema": "dbo", "target_object": "Student",
            },),
        )
        self.assertFalse(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_DENIED_STATUS)
        self.assertIn("LINKED_SERVER_DEPENDENCY", eligibility.reasons)

    def assert_external_primitive_denied(self, primitive: str) -> None:
        eligibility = self.eligibility(
            definition=(
                "CREATE VIEW reporting.CurrentStudents AS SELECT * FROM "
                f"{primitive}(RemoteSource, 'SELECT StudentId FROM dbo.Student')"
            ),
        )
        self.assertFalse(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_DENIED_STATUS)
        self.assertIn(f"EXTERNAL_QUERY_PRIMITIVE_{primitive}", eligibility.reasons)

    def test_openquery_view_is_denied(self) -> None:
        self.assert_external_primitive_denied("OPENQUERY")

    def test_openrowset_view_is_denied(self) -> None:
        self.assert_external_primitive_denied("OPENROWSET")

    def test_opendatasource_view_is_denied(self) -> None:
        self.assert_external_primitive_denied("OPENDATASOURCE")

    def test_external_synonym_view_reference_is_denied(self) -> None:
        eligibility = self.eligibility(
            dependencies=({
                "source_schema": "reporting", "source_object": "CurrentStudents",
                "target_schema": "dbo", "target_object": "RemoteStudent",
                "referenced_id": 55,
            },),
            synonyms=({
                "schema_name": "dbo", "object_name": "RemoteStudent",
                "base_object_name": "[LinkedSrv].[OtherDb].[dbo].[Student]",
            },),
        )
        self.assertFalse(eligibility.allowed)
        self.assertEqual(eligibility.status, VIEW_SAMPLE_DENIED_STATUS)
        self.assertIn("EXTERNAL_SYNONYM_DEPENDENCY", eligibility.reasons)

    def test_unavailable_encrypted_opaque_dynamic_and_unresolved_view_evidence_fails_closed(self) -> None:
        cases = {
            "unavailable": self.eligibility(
                definition="",
                view_updates={"definition_available": False},
            ),
            "encrypted": self.eligibility(
                view_updates={"is_encrypted": True},
            ),
            "opaque": self.eligibility(
                view_updates={"definition_opaque": True},
            ),
            "dynamic": self.eligibility(
                view_updates={"dynamic_sql_present": True},
            ),
            "dependency_failure": self.eligibility(
                dependency_discovery_complete=False,
            ),
            "unresolved": self.eligibility(
                dependencies=({
                    "source_schema": "reporting", "source_object": "CurrentStudents",
                    "target_schema": "dbo", "target_object": "UnknownObject",
                    "referenced_id": "",
                },),
            ),
        }
        for name, eligibility in cases.items():
            with self.subTest(name=name):
                self.assertFalse(eligibility.allowed)
                self.assertEqual(eligibility.status, VIEW_SAMPLE_DENIED_STATUS)

    def test_table_sampling_is_unaffected_without_view_evidence(self) -> None:
        plan = build_sample_plan(
            schema_name="dbo", object_name="Student", object_type="USER_TABLE",
            requested_rows=5, sample_tables=True, sample_views=True,
            sample_large_tables=True, estimated_rows=10,
            profile_large_table_threshold=100,
        )
        self.assertTrue(plan.enabled)
        self.assertEqual(plan.status, "READY")
        validate_read_only_sql(plan.sql)

    def test_view_gate_introduces_no_remote_connection_helper(self) -> None:
        root = Path(__file__).parents[1] / "src" / "mssql_database_documenter"
        sampler_source = (root / "profiling" / "sampler.py").read_text(encoding="utf-8").casefold()
        stages_source = (root / "profiling" / "stages.py").read_text(encoding="utf-8").casefold()
        self.assertNotIn("import pyodbc", sampler_source)
        self.assertNotIn("from ..connection", sampler_source)
        self.assertNotIn("from ..connection", stages_source)

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
                "views": [{
                    "schema_name": "reporting", "object_name": "StudentView",
                    "definition_available": True,
                    "definition_sanitized": "CREATE VIEW reporting.StudentView AS SELECT EmailAddress FROM dbo.Student",
                    "dynamic_sql_present": False,
                }],
                "dependencies": [{
                    "source_schema": "reporting", "source_object": "StudentView",
                    "target_schema": "dbo", "target_object": "Student",
                    "referenced_id": 42,
                }],
                "static_references": [], "synonyms": [],
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
                "views": [{
                    "schema_name": "reporting", "object_name": "SlowView",
                    "definition_available": True,
                    "definition_sanitized": "CREATE VIEW reporting.SlowView AS SELECT StudNm FROM dbo.Student",
                    "dynamic_sql_present": False,
                }],
                "dependencies": [{
                    "source_schema": "reporting", "source_object": "SlowView",
                    "target_schema": "dbo", "target_object": "Student",
                    "referenced_id": 42,
                }],
                "static_references": [], "synonyms": [],
            }
            run.fetch_dynamic = MagicMock(side_effect=RuntimeError("HYT00 query timeout"))
            run.prompt08_samples()
            with run.artifact("SAMPLE_INDEX.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["status"], "FAILED_TIMEOUT")
            self.assertEqual(row["returned_rows"], "0")
            self.assertEqual(row["object_type"], "VIEW")

    def test_external_view_is_skipped_in_safe_and_full_modes_with_coverage(self) -> None:
        for mode in ("safe-profile", "full-readonly"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                run = SequentialRun(
                    Settings(
                        server="sql01", databases=("School",),
                        output_root=Path(directory) / "output",
                        discovery_mode=mode, sample_tables=False, sample_views=True,
                    ),
                    "School",
                )
                run.data = {
                    "columns": [{
                        "schema_name": "reporting", "object_name": "ExternalView",
                        "object_type": "VIEW", "column_name": "StudNm",
                        "column_id": 1, "data_type": "nvarchar",
                    }],
                    "views": [{
                        "schema_name": "reporting", "object_name": "ExternalView",
                        "definition_available": True,
                        "definition_sanitized": "CREATE VIEW reporting.ExternalView AS SELECT StudNm FROM OtherDb.dbo.Student",
                        "dynamic_sql_present": False,
                    }],
                    "dependencies": [{
                        "source_schema": "reporting", "source_object": "ExternalView",
                        "target_database": "OtherDb", "target_schema": "dbo",
                        "target_object": "Student", "referenced_id": "",
                    }],
                    "static_references": [], "synonyms": [],
                    "table_sizes": [], "primary_keys": [], "indexes": [],
                    "extended_properties": [],
                }
                run.fetch_dynamic = MagicMock(
                    side_effect=AssertionError("external view queried"),
                )
                run.prompt08_samples()
                run.fetch_dynamic.assert_not_called()
                row = run.data["sample_index"][0]
                self.assertEqual(row["status"], VIEW_SAMPLE_DENIED_STATUS)
                self.assertIn("CROSS_DATABASE_DEPENDENCY", row["eligibility_reason"])
                with run.artifact("SAMPLE_INDEX.csv").open(
                    "r", encoding="utf-8-sig", newline="",
                ) as handle:
                    persisted = next(csv.DictReader(handle))
                self.assertEqual(persisted["status"], VIEW_SAMPLE_DENIED_STATUS)
                self.assertEqual(persisted["returned_rows"], "0")
                run._write_control_files(final=False)
                coverage = run.artifact("DISCOVERY_COVERAGE.md").read_text(
                    encoding="utf-8",
                )
                self.assertIn(f"{VIEW_SAMPLE_DENIED_STATUS}=1", coverage)

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
