import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
