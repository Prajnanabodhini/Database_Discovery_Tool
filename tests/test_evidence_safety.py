import csv
import json
from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.evidence_safety import audit_run_evidence
from mssql_database_documenter.git_export import GitExportError, create_git_export


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_profile_run(root: Path, value: str) -> Path:
    run = root / "output" / "School" / "run_1"
    metadata = run / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    (metadata / "manifest.json").write_text(json.dumps({"database": "School", "run_id": "1"}), encoding="utf-8")
    identity = {"schema_name": "dbo", "object_name": "Person", "column_name": "EmailAddress"}
    write_csv(
        run / "13_Data_Profiling" / "SENSITIVITY_CLASSIFICATION.csv",
        ("schema_name", "object_name", "column_name", "sensitivity_category", "masking_action"),
        [{**identity, "sensitivity_category": "PII", "masking_action": "PSEUDONYMIZE"}],
    )
    write_csv(
        run / "13_Data_Profiling" / "COLUMN_PROFILE.csv",
        ("schema_name", "object_name", "column_name", "sensitivity_category", "minimum_value", "maximum_value"),
        [{**identity, "sensitivity_category": "PII", "minimum_value": value, "maximum_value": value}],
    )
    write_csv(
        run / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv",
        ("schema_name", "object_name", "column_name", "sensitivity_category", "value"),
        [{**identity, "sensitivity_category": "PII", "value": value}],
    )
    return run


class EvidenceSafetyTests(unittest.TestCase):
    def test_raw_sensitive_profile_values_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = write_profile_run(Path(directory), "person@example.test")
            audit = audit_run_evidence(run)
            self.assertFalse(audit.passed)
            self.assertFalse(audit.checks["profile_values_masked"])
            self.assertGreaterEqual(len(audit.violations), 3)

    def test_masked_sensitive_profile_values_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = write_profile_run(Path(directory), "[MASKED:0123456789abcdef]")
            audit = audit_run_evidence(run)
            self.assertTrue(audit.passed, audit.violations)
            self.assertEqual(audit.sensitive_values_checked, 3)

    def test_unsafe_git_export_is_rejected_without_partial_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = write_profile_run(base, "person@example.test")
            with self.assertRaises(GitExportError):
                create_git_export(run, output_root=base / "output", git_export_root=base / "git_export")
            self.assertFalse((base / "git_export").exists())


if __name__ == "__main__":
    unittest.main()
