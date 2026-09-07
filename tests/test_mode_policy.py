import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.mode_policy import (
    FULL_PROFILE_HARD_CEILING,
    ModePolicyError,
    resolve_mode_policy,
)


def profile_data(row_count: int) -> dict[str, list[dict[str, object]]]:
    return {
        "columns": [{
            "schema_name": "dbo", "object_name": "Fact", "column_name": "Value",
            "data_type": "int", "object_type": "USER_TABLE", "is_computed": False,
            "column_id": 1,
        }],
        "table_sizes": [{"schema_name": "dbo", "object_name": "Fact", "row_count": row_count}],
        "extended_properties": [],
    }


class ModePolicyTests(unittest.TestCase):
    def test_four_modes_have_truthful_distinct_contracts(self) -> None:
        settings = Settings(profile_exact_row_counts=True)
        metadata = resolve_mode_policy(settings, "metadata")
        logic = resolve_mode_policy(settings, "metadata+logic")
        safe = resolve_mode_policy(settings, "safe-profile")
        full = resolve_mode_policy(settings, "full-readonly")

        self.assertFalse(metadata.permits_data_scans)
        self.assertFalse(metadata.programmable_logic)
        self.assertFalse(logic.permits_data_scans)
        self.assertTrue(logic.programmable_logic)
        self.assertTrue(logic.pipeline_metadata)
        self.assertTrue(safe.data_profiles)
        self.assertTrue(safe.samples)
        self.assertTrue(safe.relationship_validation)
        self.assertFalse(safe.exact_counts)
        self.assertFalse(safe.extended_full_validation)
        self.assertTrue(full.extended_full_validation)
        self.assertTrue(full.exact_counts)
        self.assertGreater(full.sample_row_limit, safe.sample_row_limit)
        self.assertGreater(full.profile_row_threshold, safe.profile_row_threshold)
        self.assertGreater(full.relationship_validation_threshold, safe.relationship_validation_threshold)
        self.assertGreater(full.low_cardinality_limit, safe.low_cardinality_limit)

    def test_metadata_modes_do_not_exact_count_even_if_requested(self) -> None:
        for mode in ("metadata", "metadata+logic"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                run = SequentialRun(
                    Settings(
                        discovery_mode=mode, profile_exact_row_counts=True,
                        server="sql01", databases=("School",), output_root=Path(directory) / "output",
                    ),
                    "School",
                )
                run.data = profile_data(10)
                run.fetch_dynamic = MagicMock()
                run.prompt06_size_shape()
                run.fetch_dynamic.assert_not_called()
                self.assertFalse(run.mode_policy.permits_data_scans)

    def test_safe_and_full_profile_take_different_runtime_branches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            safe = SequentialRun(
                Settings(
                    discovery_mode="safe-profile", server="sql01", databases=("School",),
                    output_root=base / "safe",
                ),
                "School",
            )
            safe.data = profile_data(2_000_000)
            safe.fetch_dynamic = MagicMock()
            safe.prompt07_profile()
            safe.fetch_dynamic.assert_not_called()
            self.assertEqual(safe.data["column_profile"][0]["profile_status"], "SKIPPED_FOR_SAFETY_LARGE_TABLE")

            full = SequentialRun(
                Settings(
                    discovery_mode="full-readonly", server="sql01", databases=("School",),
                    output_root=base / "full",
                ),
                "School",
            )
            full.data = profile_data(2_000_000)
            full.fetch_dynamic = MagicMock(side_effect=[
                [{"total_rows": 2_000_000, "non_null_count": 2_000_000, "distinct_count": 1, "minimum_value": "1", "maximum_value": "1", "zero_count": 0, "negative_count": 0, "average_numeric": 1, "standard_deviation_numeric": 0}],
                [{"value": "1", "value_count": 2_000_000}],
            ])
            full.prompt07_profile()
            self.assertEqual(full.data["column_profile"][0]["profile_status"], "PROFILED")
            self.assertEqual(full.fetch_dynamic.call_count, 2)

    def test_exact_counts_are_full_readonly_only_and_ceiling_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            safe = SequentialRun(
                Settings(
                    discovery_mode="safe-profile", profile_exact_row_counts=True,
                    server="sql01", databases=("School",), output_root=base / "safe",
                ),
                "School",
            )
            safe.data = profile_data(10)
            safe.fetch_dynamic = MagicMock()
            safe.prompt06_size_shape()
            safe.fetch_dynamic.assert_not_called()

            full = SequentialRun(
                Settings(
                    discovery_mode="full-readonly", profile_exact_row_counts=True,
                    server="sql01", databases=("School",), output_root=base / "full",
                ),
                "School",
            )
            full.data = profile_data(10)
            full.fetch_dynamic = MagicMock(return_value=[{"exact_rows": 11}])
            full.prompt06_size_shape()
            full.fetch_dynamic.assert_called_once()
            self.assertEqual(full.data["table_shape"][0]["row_count_type"], "EXACT")

    def test_hard_ceiling_rejects_before_run_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            settings = Settings(
                discovery_mode="full-readonly",
                full_readonly_profile_threshold=FULL_PROFILE_HARD_CEILING + 1,
                output_root=output,
            )
            with self.assertRaises(ModePolicyError):
                SequentialRun(settings, "School")
            self.assertFalse(output.exists())

    def test_full_readonly_cannot_resolve_shallower_than_safe_profile(self) -> None:
        with self.assertRaises(ModePolicyError):
            resolve_mode_policy(Settings(full_readonly_sample_row_limit=99), "full-readonly")
        with self.assertRaises(ModePolicyError):
            resolve_mode_policy(Settings(
                full_readonly_sample_row_limit=100,
                full_readonly_profile_threshold=1_000_000,
                full_readonly_relationship_threshold=1_000_000,
                full_readonly_low_cardinality_limit=50,
                full_readonly_extended_validation=False,
                profile_exact_row_counts=False,
            ), "full-readonly")

    def test_resolved_policy_is_persisted_in_all_three_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(
                    discovery_mode="safe-profile", server="sql01", databases=("School",),
                    output_root=Path(directory) / "output",
                ),
                "School",
            )
            run.prompt20_environment()
            run._snapshot_integrity()
            configuration = json.loads(run.artifact("RUN_CONFIGURATION.json").read_text(encoding="utf-8"))
            summary = json.loads(run.artifact("run_summary.json").read_text(encoding="utf-8"))
            manifest = json.loads(run.artifact("manifest.json").read_text(encoding="utf-8"))
            for payload in (configuration, summary, manifest):
                self.assertEqual(payload["resolved_mode_policy"]["mode"], "safe-profile")
                self.assertTrue(payload["resolved_mode_policy"]["permits_data_scans"])


if __name__ == "__main__":
    unittest.main()
