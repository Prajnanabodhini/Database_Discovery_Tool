from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import main as launcher
from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.selftest import SELF_TEST_ARGV, run_self_test


class RuntimeSelfTestDecouplingTests(unittest.TestCase):
    def test_live_run_review_never_invokes_pytest_or_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(output_root=Path(directory) / "output"),
                "SchoolERP",
            )
            run.data = {
                "tables": [], "columns": [], "views": [], "procedures": [],
                "functions": [], "triggers": [], "foreign_keys": [],
                "inferred_relationships": [], "lineage": [], "risks": [],
                "pipelines": [], "sample_rows": {}, "column_profile": [],
            }
            run._ensure_contract_files()
            for name in ("manifest.json", "checksums.sha256", "STAGE_STATUS.json", "RUN_CONFIGURATION.json"):
                path = run.artifact(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")

            with patch.dict(sys.modules, {"pytest": None}), \
                 patch("subprocess.run", side_effect=AssertionError("runtime invoked a subprocess")) as invoked:
                run.prompt21_review()

            invoked.assert_not_called()
            review = (run.root / "99_Git_Handoff" / "FINAL_CODE_REVIEW.md").read_text(encoding="utf-8")
            self.assertIn("Developer pytest invoked during discovery: no", review)
            self.assertIn("Current-run semantic invariants", review)
            self.assertNotIn("| `tests/", review)

    def test_explicit_self_test_uses_fixed_argv_without_shell_or_runtime_roots(self) -> None:
        completed = subprocess.CompletedProcess(
            args=SELF_TEST_ARGV,
            returncode=0,
            stdout="141 passed, 2 skipped in 4.53s\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("mssql_database_documenter.selftest.subprocess.run", return_value=completed) as invoked, \
                 patch("mssql_database_documenter.connection.connect") as connect, \
                 patch("mssql_database_documenter.inventory._new_run_directory") as new_run:
                result = run_self_test(project_root=root)

            invoked.assert_called_once()
            argv = invoked.call_args.args[0]
            self.assertEqual(tuple(argv), SELF_TEST_ARGV)
            self.assertEqual(
                SELF_TEST_ARGV[1:],
                ("-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not live", "tests"),
            )
            self.assertFalse(invoked.call_args.kwargs["shell"])
            self.assertEqual(Path(invoked.call_args.kwargs["cwd"]).resolve(), root.resolve())
            connect.assert_not_called()
            new_run.assert_not_called()
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["pytest_invoked"])
            self.assertFalse(result["connection_attempted"])
            self.assertFalse((root / "output").exists())
            self.assertFalse((root / "git_export").exists())

    def test_self_test_failure_summary_is_sanitized(self) -> None:
        secret = "prompt09-fake-secret"
        completed = subprocess.CompletedProcess(
            args=SELF_TEST_ARGV,
            returncode=1,
            stdout="",
            stderr=f"database fixture failed password={secret}",
        )
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"MSSQL_PASSWORD": secret}), \
             patch("mssql_database_documenter.selftest.subprocess.run", return_value=completed):
            result = run_self_test(project_root=Path(directory))

        self.assertEqual(result["status"], "FAIL")
        self.assertNotIn(secret, result["summary"])
        self.assertIn("[REDACTED]", result["summary"])

    def test_main_self_test_bypasses_environment_and_reports_sanitized_result(self) -> None:
        expected = {
            "status": "PASS", "scope": "offline-developer-tests",
            "pytest_invoked": True, "connection_attempted": False,
            "output_or_export_created": False, "returncode": 0,
            "summary": "tests passed",
        }
        output = StringIO()
        with patch("mssql_database_documenter.selftest.run_self_test", return_value=expected) as run, \
             patch("mssql_database_documenter.config.Settings.from_environment") as load_settings, \
             redirect_stdout(output):
            returncode = launcher.main(["self-test"])

        self.assertEqual(returncode, 0)
        run.assert_called_once_with(project_root=launcher.PROJECT_ROOT)
        load_settings.assert_not_called()
        self.assertEqual(json.loads(output.getvalue()), expected)


if __name__ == "__main__":
    unittest.main()
