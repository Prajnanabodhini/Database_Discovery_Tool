import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from mssql_database_documenter.comparison.engine import CATALOGUES
from mssql_database_documenter.config import Settings
from mssql_database_documenter.contracts import DISCOVERY_CAPABILITY_MATRIX, EXTRA_OUTPUTS, REQUIRED_OUTPUTS
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.inventory import run_inventory
from mssql_database_documenter.metadata.support import (
    FEATURE_SUPPORT_STATES,
    is_unsupported_metadata_error,
    support_record,
)
from mssql_database_documenter.queries import METADATA_QUERIES, SECURITY_METADATA_QUERIES
from mssql_database_documenter.safety import validate_read_only_sql


EXPECTED_FAMILIES = {
    "database_files",
    "filegroups",
    "partition_functions",
    "partition_schemes",
    "partition_compression",
    "user_defined_types",
    "statistics",
    "fulltext_catalogs",
    "fulltext_indexes",
    "cdc_status",
    "change_tracking_status",
    "database_scoped_configurations",
    "xml_schema_collections",
}

EXPECTED_COMPARISONS = EXPECTED_FAMILIES | {"security_principals", "mssql_feature_support"}


class MetadataCompletenessTests(unittest.TestCase):
    def test_all_required_metadata_families_are_registered_and_safe(self) -> None:
        families = {query.feature_family for query in METADATA_QUERIES if query.feature_family}
        self.assertEqual(families, EXPECTED_FAMILIES)
        for query in METADATA_QUERIES + SECURITY_METADATA_QUERIES:
            with self.subTest(query=query.name):
                validate_read_only_sql(query.sql)
                self.assertTrue(query.columns)
                self.assertEqual(len(query.columns), len(set(query.columns)))
                self.assertTrue(query.output_folder)
                self.assertTrue(query.output_name.endswith(".csv"))

    def test_every_family_artifact_has_contract_and_capability(self) -> None:
        artifacts = set(REQUIRED_OUTPUTS) | set(EXTRA_OUTPUTS)
        capability_artifacts = {
            artifact
            for names in DISCOVERY_CAPABILITY_MATRIX.values()
            for artifact in names
        }
        for query in METADATA_QUERIES + SECURITY_METADATA_QUERIES:
            if not query.feature_family:
                continue
            with self.subTest(query=query.name):
                self.assertIn(query.output_name, artifacts)
                self.assertIn(query.output_name, capability_artifacts)
        self.assertIn("MSSQL_FEATURE_SUPPORT_OVERVIEW.csv", artifacts)
        self.assertIn("MSSQL_FEATURE_SUPPORT_OVERVIEW.md", artifacts)

    def test_feature_support_states_are_explicit_and_fail_closed(self) -> None:
        query = next(item for item in METADATA_QUERIES if item.name == "filegroups")
        self.assertEqual(support_record(query, row_count=1)["status"], "PRESENT")
        self.assertEqual(support_record(query, row_count=0)["status"], "ABSENT")
        self.assertEqual(support_record(query, row_count=0, state="INACCESSIBLE")["status"], "INACCESSIBLE")
        self.assertEqual(support_record(query, row_count=0, state="UNSUPPORTED")["status"], "UNSUPPORTED")
        self.assertTrue({"PRESENT", "ABSENT", "INACCESSIBLE", "UNSUPPORTED"}.issubset(FEATURE_SUPPORT_STATES))
        self.assertTrue(is_unsupported_metadata_error("Invalid object name 'sys.database_scoped_configurations'"))
        self.assertFalse(is_unsupported_metadata_error("SELECT permission denied"))

    def test_full_runner_writes_every_artifact_and_truthful_states(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(output_root=Path(directory) / "output"),
                "SchoolERP",
            )

            def fake_fetch(query, **_):
                if query.name == "tables":
                    return [{"schema_name": "dbo", "object_name": "Student", "object_id": 1}]
                if query.name == "columns":
                    return [{"schema_name": "dbo", "object_name": "Student", "object_id": 1, "column_id": 1, "column_name": "Id"}]
                if query.name == "database_files":
                    return [{"server_name": "[SANITIZED]", "database_name": "SchoolERP", "file_id": 1, "file_name": "SchoolERP", "file_type": "ROWS"}]
                if query.name == "database_scoped_configurations":
                    raise RuntimeError("Invalid object name 'sys.database_scoped_configurations'")
                if query.name == "statistics":
                    run.errors.append({"query_name": query.name, "sanitized_message": "SELECT permission denied"})
                return []

            run.fetch = MagicMock(side_effect=fake_fetch)
            run.prompt04_metadata()
            states = {row["query_name"]: row["status"] for row in run.data["metadata_feature_support"]}
            self.assertEqual(states["database_files"], "PRESENT")
            self.assertEqual(states["filegroups"], "ABSENT")
            self.assertEqual(states["statistics"], "INACCESSIBLE")
            self.assertEqual(states["database_scoped_configurations"], "UNSUPPORTED")
            self.assertEqual(states["security_principals"], "DISABLED")
            for query in METADATA_QUERIES + SECURITY_METADATA_QUERIES:
                self.assertTrue((run.root / query.output_folder / query.output_name).is_file())
            overview = run.artifact("MSSQL_FEATURE_SUPPORT_OVERVIEW.csv")
            with overview.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), len(EXPECTED_FAMILIES) + 1)
            self.assertTrue(run.artifact("MSSQL_FEATURE_SUPPORT_OVERVIEW.md").is_file())

    def test_security_metadata_is_opt_in_and_identity_is_hashed(self) -> None:
        self.assertFalse(Settings().discover_security_metadata)
        enabled = Settings.from_environment(
            env={"DISCOVER_SECURITY_METADATA": "true"},
            dotenv_path=None,
        )
        self.assertTrue(enabled.discover_security_metadata)
        self.assertTrue(enabled.sanitized()["discover_security_metadata"])
        self.assertEqual(len(SECURITY_METADATA_QUERIES), 1)
        query = SECURITY_METADATA_QUERIES[0]
        self.assertEqual(query.optional_setting, "discover_security_metadata")
        self.assertIn("HASHBYTES('SHA2_256'", query.sql)
        self.assertIn("principal_name_sha256", query.columns)
        self.assertNotIn("principal_name", query.columns)
        self.assertNotIn("permission", query.sql.casefold())

    def test_metadata_only_runner_persists_absent_inaccessible_and_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(
                server="sql01", databases=("SchoolERP",),
                output_root=Path(directory) / "output",
            )
            connection = MagicMock()

            def fake_fetch(_cursor, query):
                if query.name == "database_files":
                    return [{"file_id": 1}]
                if query.name == "statistics":
                    raise PermissionError("SELECT permission denied")
                if query.name == "database_scoped_configurations":
                    raise RuntimeError("Invalid object name 'sys.database_scoped_configurations'")
                return []

            with patch("mssql_database_documenter.inventory.connect") as connect_mock, patch(
                "mssql_database_documenter.inventory._fetch", side_effect=fake_fetch
            ):
                connect_mock.return_value.__enter__.return_value = connection
                result = run_inventory(settings, "SchoolERP")
            with (result.run_directory / "02_Server_Database" / "MSSQL_FEATURE_SUPPORT_OVERVIEW.csv").open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                states = {row["query_name"]: row["status"] for row in csv.DictReader(handle)}
            self.assertEqual(states["database_files"], "PRESENT")
            self.assertEqual(states["filegroups"], "ABSENT")
            self.assertEqual(states["statistics"], "INACCESSIBLE")
            self.assertEqual(states["database_scoped_configurations"], "UNSUPPORTED")
            self.assertEqual(states["security_principals"], "DISABLED")
            self.assertEqual(result.query_count, len(METADATA_QUERIES))

    def test_enabled_security_catalogue_discards_unregistered_raw_identity_fields(self) -> None:
        fake_identity = "FakePrincipalSecret"
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(
                    output_root=Path(directory) / "output",
                    discover_security_metadata=True,
                ),
                "SchoolERP",
            )

            def fake_fetch(query, **_):
                if query.name == "tables":
                    return [{"schema_name": "dbo", "object_name": "Student", "object_id": 1}]
                if query.name == "columns":
                    return [{"schema_name": "dbo", "object_name": "Student", "object_id": 1, "column_id": 1, "column_name": "Id"}]
                if query.name == "security_principals":
                    return [{
                        "principal_id": 7,
                        "principal_name_sha256": "A" * 64,
                        "principal_name": fake_identity,
                    }]
                return []

            run.fetch = MagicMock(side_effect=fake_fetch)
            run.prompt04_metadata()
            persisted = run.artifact("SECURITY_PRINCIPALS.csv").read_text(encoding="utf-8-sig")
            self.assertNotIn(fake_identity, persisted)
            self.assertNotIn("principal_name", run.data["security_principals"][0])
            self.assertEqual(run.data["security_principals"][0]["principal_name_sha256"], "A" * 64)

    def test_database_file_catalogue_omits_physical_paths(self) -> None:
        query = next(item for item in METADATA_QUERIES if item.name == "database_files")
        self.assertNotIn("physical_name", query.columns)
        self.assertNotIn("physical_name", query.sql.casefold())

    def test_comparison_engine_registers_every_meaningful_category(self) -> None:
        self.assertTrue(EXPECTED_COMPARISONS.issubset(CATALOGUES))


if __name__ == "__main__":
    unittest.main()
