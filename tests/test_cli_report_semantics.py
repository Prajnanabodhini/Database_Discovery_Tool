import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import main as launcher
from mssql_database_documenter.cli import main as cli_main


def hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def manifested_run(output_root: Path, *, name: str = "run_20260907_120000") -> Path:
    run = output_root / "School" / name
    metadata = run / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    manifest = {
        "run_id": name.removeprefix("run_"),
        "database": "School",
        "configuration": {"server": "[SANITIZED]", "discovery_mode": "metadata+logic"},
        "stages": [{"prompt": "02", "status": "PASS"}],
        "warnings": [],
    }
    (metadata / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (metadata / "run_summary.json").write_text(json.dumps({
        "run_id": manifest["run_id"], "database": "School", "mode": "metadata+logic",
        "status": "COMPLETED", "warning_error_count": 0,
    }), encoding="utf-8")
    summary = run / "01_Executive_Summary" / "MSSQL_EXECUTIVE_SUMMARY.md"
    summary.parent.mkdir()
    summary.write_text("# Canonical report\n", encoding="utf-8")
    return run


class CliReportSemanticsTests(unittest.TestCase):
    def test_help_distinguishes_live_discovery_from_offline_regeneration_without_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed = subprocess.run(
                [sys.executable, "-m", "mssql_database_documenter", "--help"],
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            normalized_help = " ".join(completed.stdout.split())
            self.assertIn("new live read-only discovery", normalized_help)
            self.assertIn("offline from one existing manifested output run", normalized_help)
            self.assertIn("discover-and-report", completed.stdout)
            self.assertIn("regenerate-reports", completed.stdout)
            self.assertNotIn("\n    report ", completed.stdout)
            self.assertFalse((root / "output").exists())
            self.assertFalse((root / "git_export").exists())

    def test_offline_cli_regeneration_is_contained_versioned_and_source_preserving(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_root = root / "output"
            source = manifested_run(output_root)
            before = hashes(source)
            env_file = root / ".env"
            env_file.write_text(
                f"OUTPUT_ROOT={output_root}\nMSSQL_SERVER=private-sql\n"
                "MSSQL_TRUSTED_CONNECTION=false\nMSSQL_USERNAME=operator\n"
                "MSSQL_PASSWORD=cli-secret\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with (
                patch(
                    "mssql_database_documenter.connection.connect",
                    side_effect=AssertionError("database connection attempted"),
                ) as connect,
                redirect_stdout(stdout),
            ):
                result = cli_main([
                    "--env-file", str(env_file), "regenerate-reports",
                    "--run", "output:School/run_20260907_120000",
                ])
            self.assertEqual(result, 0)
            connect.assert_not_called()
            self.assertEqual(hashes(source), before)
            payload = json.loads(stdout.getvalue())
            self.assertNotIn("private-sql", stdout.getvalue())
            self.assertNotIn("operator", stdout.getvalue())
            self.assertNotIn("cli-secret", stdout.getvalue())
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["operation"], "offline-report-regeneration")
            self.assertFalse(payload["database_connection_attempted"])
            self.assertFalse(payload["canonical_source_mutated"])
            destination = Path(payload["outputs"]["destination"]).resolve()
            destination.relative_to(output_root.resolve())
            self.assertEqual(destination.parents[2], (output_root / "report_regenerations").resolve())
            self.assertTrue(destination.name.startswith("regen_"))
            self.assertTrue(Path(payload["outputs"]["manifest"]).is_file())
            self.assertTrue(Path(payload["outputs"]["checksums"]).is_file())

    def test_regeneration_rejects_source_outside_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_root = root / "output"
            output_root.mkdir()
            outside = manifested_run(root / "outside")
            env_file = root / ".env"
            env_file.write_text(f"OUTPUT_ROOT={output_root}\n", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                result = cli_main([
                    "--env-file", str(env_file), "regenerate-reports",
                    "--run", str(outside),
                ])
            self.assertEqual(result, 2)
            self.assertFalse((output_root / "report_regenerations").exists())

    def test_regeneration_requires_a_manifested_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_root = root / "output"
            unmanifested = output_root / "School" / "run_missing_manifest"
            unmanifested.mkdir(parents=True)
            env_file = root / ".env"
            env_file.write_text(f"OUTPUT_ROOT={output_root}\n", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                result = cli_main([
                    "--env-file", str(env_file), "regenerate-reports",
                    "--run", str(unmanifested),
                ])
            self.assertEqual(result, 2)
            self.assertFalse((output_root / "report_regenerations").exists())

    def test_all_discovery_dispatch_is_unchanged_and_alias_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("DISCOVERY_MODE=metadata\n", encoding="utf-8")
            for command in ("all", "discover-and-report"):
                with self.subTest(command=command), patch(
                    "mssql_database_documenter.fullrun.run_all",
                    return_value=[Path("output/School/run_test")],
                ) as run_all, redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        cli_main(["--env-file", str(env_file), command]),
                        0,
                    )
                    run_all.assert_called_once()

    def test_legacy_report_command_is_not_accepted(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            cli_main(["report"])
        self.assertEqual(raised.exception.code, 2)

    def test_top_level_launcher_forwards_offline_regeneration_explicitly(self) -> None:
        with patch("mssql_database_documenter.cli.main", return_value=0) as package_cli:
            self.assertEqual(launcher.main([
                "--env-file", "operator.env", "regenerate-reports",
                "--run", "output:School/run_1",
            ]), 0)
        package_cli.assert_called_once_with([
            "--env-file", "operator.env", "regenerate-reports",
            "--run", "output:School/run_1",
        ])


if __name__ == "__main__":
    unittest.main()
