import csv
import hashlib
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


def sample_run(base: Path) -> tuple[Path, Path]:
    run = base / "output" / "School" / "run_20260101"
    metadata = run / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    (metadata / "manifest.json").write_text(
        json.dumps({"database": "School", "run_id": "20260101", "configuration": {}, "files": []}),
        encoding="utf-8",
    )
    sample = run / "14_Samples" / "dbo__Student.csv"
    write_csv(sample, ("StudentId", "StudNm"), [{"StudentId": 7, "StudNm": "Alice Example"}])
    write_csv(
        run / "14_Samples" / "MASKING_REPORT.csv",
        ("schema_name", "object_name", "column_name", "category"),
        [{"schema_name": "dbo", "object_name": "Student", "column_name": "StudNm", "category": "PII"}],
    )
    write_csv(
        run / "14_Samples" / "SAMPLE_INDEX.csv",
        ("schema_name", "object_name", "sample_file"),
        [{"schema_name": "dbo", "object_name": "Student", "sample_file": sample.name}],
    )
    handoff = run / "99_Git_Handoff"
    handoff.mkdir(parents=True)
    (handoff / "SAFE_TO_COMMIT_CHECKLIST.md").write_text("# Safe to Commit Checklist\n", encoding="utf-8")
    return run, sample


def profile_run(base: Path) -> Path:
    run, _ = sample_run(base)
    identities = [
        ("Value1", "Unknown", "NO_SENSITIVITY_SIGNAL", "nvarchar", "Alice Example", "Zara Example"),
        ("Value2", "Unknown", "NO_SENSITIVITY_SIGNAL", "nvarchar", "42 Example Street", "99 Sample Road"),
        ("EmailAddress", "PII", "BUILTIN_COLUMN_NAME", "nvarchar", "a@example.test", "z@example.test"),
        ("PasswordValue", "Credential", "BUILTIN_COLUMN_NAME", "nvarchar", "hunter2", "open-sesame"),
        ("ReviewedName", "Non-sensitive", "OVERRIDE: operator-reviewed label", "nvarchar", "Active", "Inactive"),
        ("SequenceValue", "Unknown", "NO_SENSITIVITY_SIGNAL", "int", "1", "900"),
        ("BinaryValue", "Unknown", "NO_SENSITIVITY_SIGNAL", "varbinary", "0x0102", "0xFEFF"),
    ]
    write_csv(
        run / "13_Data_Profiling" / "SENSITIVITY_CLASSIFICATION.csv",
        ("schema_name", "object_name", "column_name", "sensitivity_category", "masking_action", "evidence"),
        [
            {
                "schema_name": "dbo", "object_name": "ProfileFixture", "column_name": column,
                "sensitivity_category": category,
                "masking_action": "REDACT" if category == "Credential" else "PRESERVE",
                "evidence": evidence,
            }
            for column, category, evidence, _, _, _ in identities
        ],
    )
    write_csv(
        run / "13_Data_Profiling" / "COLUMN_PROFILE.csv",
        (
            "schema_name", "object_name", "column_name", "data_type",
            "sensitivity_category", "sensitivity_evidence", "minimum_value",
            "maximum_value", "total_rows", "null_percent", "distinct_count", "profile_status",
        ),
        [
            {
                "schema_name": "dbo", "object_name": "ProfileFixture", "column_name": column,
                "data_type": data_type, "sensitivity_category": category,
                "sensitivity_evidence": evidence, "minimum_value": minimum,
                "maximum_value": maximum, "total_rows": 10, "null_percent": 0,
                "distinct_count": 2, "profile_status": "PROFILED",
            }
            for column, category, evidence, data_type, minimum, maximum in identities
        ],
    )
    write_csv(
        run / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv",
        (
            "schema_name", "object_name", "column_name", "sensitivity_category",
            "sensitivity_evidence", "value", "value_count", "total_rows", "value_percent",
        ),
        [{
            "schema_name": "dbo", "object_name": "ProfileFixture", "column_name": "Value1",
            "sensitivity_category": "Unknown", "sensitivity_evidence": "NO_SENSITIVITY_SIGNAL",
            "value": "Alice Example", "value_count": 4, "total_rows": 10, "value_percent": 40,
        }],
    )
    return run


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class GitExportSamplePolicyTests(unittest.TestCase):
    def test_default_excludes_payload_but_retains_control_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run, _ = sample_run(base)
            exported = create_git_export(run, output_root=base / "output", git_export_root=base / "git_export")
            self.assertFalse((exported / "14_Samples" / "dbo__Student.csv").exists())
            self.assertTrue((exported / "14_Samples" / "MASKING_REPORT.csv").is_file())
            self.assertTrue((exported / "14_Samples" / "SAMPLE_INDEX.csv").is_file())
            policy = json.loads((exported / "99_Git_Handoff" / "GIT_EXPORT_POLICY.json").read_text(encoding="utf-8"))
            self.assertEqual(policy["sample_policy"], "exclude")
            self.assertFalse(policy["raw_sample_payloads_included"])
            manifest = json.loads((exported / "00_Run_Metadata" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["git_export"]["sample_policy"], "exclude")

    def test_masked_only_sanitizes_copy_without_mutating_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run, source = sample_run(base)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            exported = create_git_export(
                run,
                output_root=base / "output",
                git_export_root=base / "git_export",
                sample_policy="masked_only",
            )
            after = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            with (exported / "14_Samples" / source.name).open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertRegex(row["StudentId"], r"^\[MASKED:[0-9a-f]{16}\]$")
            self.assertRegex(row["StudNm"], r"^\[MASKED:[0-9a-f]{16}\]$")
            exported_text = "\n".join(
                path.read_text(encoding="utf-8-sig", errors="replace")
                for path in exported.rglob("*")
                if path.is_file()
            )
            self.assertNotIn("Alice Example", exported_text)
            checksums = exported / "00_Run_Metadata" / "checksums.sha256"
            for line in checksums.read_text(encoding="utf-8").splitlines():
                digest, relative = line.split("  ", 1)
                self.assertEqual(digest, hashlib.sha256((exported / relative).read_bytes()).hexdigest())

    def test_raw_policy_is_rejected_without_partial_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run, _ = sample_run(base)
            with self.assertRaises(GitExportError):
                create_git_export(
                    run,
                    output_root=base / "output",
                    git_export_root=base / "git_export",
                    sample_policy="raw",
                )
            self.assertFalse((base / "git_export").exists())

    def test_default_profile_policy_masks_unknown_sensitive_and_binary_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = profile_run(base)
            source_paths = (
                run / "13_Data_Profiling" / "COLUMN_PROFILE.csv",
                run / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv",
            )
            before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
            exported = create_git_export(
                run, output_root=base / "output", git_export_root=base / "git_export",
            )
            after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
            self.assertEqual(before, after)

            rows = {
                row["column_name"]: row
                for row in read_csv_rows(exported / "13_Data_Profiling" / "COLUMN_PROFILE.csv")
            }
            for column in ("Value1", "Value2", "EmailAddress"):
                self.assertRegex(rows[column]["minimum_value"], r"^\[MASKED:[0-9a-f]{16}\]$")
                self.assertRegex(rows[column]["maximum_value"], r"^\[MASKED:[0-9a-f]{16}\]$")
            self.assertEqual(rows["PasswordValue"]["minimum_value"], "[REDACTED]")
            self.assertEqual(rows["PasswordValue"]["maximum_value"], "[REDACTED]")
            self.assertEqual(rows["BinaryValue"]["minimum_value"], "[BINARY_REDACTED]")
            self.assertEqual(rows["BinaryValue"]["maximum_value"], "[BINARY_REDACTED]")
            self.assertEqual(rows["ReviewedName"]["minimum_value"], "Active")
            self.assertEqual(rows["ReviewedName"]["maximum_value"], "Inactive")
            self.assertEqual(rows["SequenceValue"]["minimum_value"], "1")
            self.assertEqual(rows["SequenceValue"]["maximum_value"], "900")
            low = read_csv_rows(exported / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv")[0]
            self.assertRegex(low["value"], r"^\[MASKED:[0-9a-f]{16}\]$")

            exported_text = "\n".join(
                path.read_text(encoding="utf-8-sig", errors="replace")
                for path in exported.rglob("*") if path.is_file()
            )
            for raw in (
                "Alice Example", "42 Example Street", "a@example.test",
                "hunter2", "0x0102",
            ):
                self.assertNotIn(raw, exported_text)
            self.assertTrue(audit_run_evidence(exported).passed)

    def test_aggregate_only_removes_payloads_and_retains_aggregate_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = profile_run(base)
            exported = create_git_export(
                run, output_root=base / "output", git_export_root=base / "git_export",
                profile_value_policy="aggregate_only",
            )
            profiles = read_csv_rows(exported / "13_Data_Profiling" / "COLUMN_PROFILE.csv")
            low = read_csv_rows(exported / "13_Data_Profiling" / "LOW_CARDINALITY_VALUES.csv")
            self.assertTrue(all(not row["minimum_value"] and not row["maximum_value"] for row in profiles))
            self.assertTrue(all(not row["value"] for row in low))
            self.assertEqual(profiles[0]["total_rows"], "10")
            self.assertEqual(profiles[0]["distinct_count"], "2")
            self.assertEqual(low[0]["value_count"], "4")
            policy = json.loads(
                (exported / "99_Git_Handoff" / "GIT_EXPORT_POLICY.json").read_text(encoding="utf-8")
            )
            self.assertEqual(policy["profile_value_policy"], "aggregate_only")
            self.assertEqual(policy["profile_values_masked"], 0)
            self.assertEqual(policy["profile_values_omitted"], 15)
            self.assertTrue(policy["profile_value_fields_withheld"])
            self.assertEqual(len(policy["withheld_profile_fields"]), 3)
            self.assertFalse(policy["source_evidence_mutated"])
            self.assertTrue(audit_run_evidence(exported).passed)

    def test_profile_policy_manifest_counters_and_checksums_are_accurate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            exported = create_git_export(
                profile_run(base), output_root=base / "output",
                git_export_root=base / "git_export",
            )
            policy = json.loads(
                (exported / "99_Git_Handoff" / "GIT_EXPORT_POLICY.json").read_text(encoding="utf-8")
            )
            manifest = json.loads(
                (exported / "00_Run_Metadata" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(policy["profile_value_policy"], "mask_unknown_text")
            self.assertEqual(policy["profile_values_masked"], 11)
            self.assertEqual(policy["profile_values_omitted"], 0)
            self.assertEqual(manifest["git_export"], policy)
            self.assertEqual(
                manifest["configuration"]["git_export_profile_value_policy"], "mask_unknown_text",
            )
            checksums = exported / "00_Run_Metadata" / "checksums.sha256"
            for line in checksums.read_text(encoding="utf-8").splitlines():
                digest, relative = line.split("  ", 1)
                self.assertEqual(digest, hashlib.sha256((exported / relative).read_bytes()).hexdigest())

    def test_independent_audit_rejects_raw_unknown_text_despite_policy_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            exported = create_git_export(
                profile_run(base), output_root=base / "output",
                git_export_root=base / "git_export",
            )
            profile = exported / "13_Data_Profiling" / "COLUMN_PROFILE.csv"
            rows = read_csv_rows(profile)
            rows[0]["minimum_value"] = "Alice Example"
            write_csv(profile, tuple(rows[0]), rows)
            audit = audit_run_evidence(exported)
            self.assertFalse(audit.passed)
            self.assertFalse(audit.checks["profile_values_masked"])

    def test_raw_profile_value_policy_is_rejected_without_partial_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = profile_run(base)
            with self.assertRaises(GitExportError):
                create_git_export(
                    run, output_root=base / "output", git_export_root=base / "git_export",
                    profile_value_policy="raw",
                )
            self.assertFalse((base / "git_export").exists())


if __name__ == "__main__":
    unittest.main()
