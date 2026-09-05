import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

import main as launcher
from mssql_database_documenter.config import ConfigurationError, Settings
from mssql_database_documenter.web.app import create_app


def write_run(output: Path, run_id: str, database: str = "School", mode: str = "metadata") -> Path:
    root = output / database / f"run_{run_id}"
    metadata = root / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    summary = {"run_id": run_id, "database": database, "server_alias": "[SANITIZED]", "timestamp_utc": "2026-01-01T00:00:00Z", "mode": mode, "status": "COMPLETED", "tool_version": "0.3.0", "sql_server_version": "16", "sample_rows": 0, "exact_row_counts": False, "completed_stage_count": 20, "warning_error_count": 0}
    (metadata / "manifest.json").write_text(json.dumps({"run_id": run_id, "database": database, "configuration": {"discovery_mode": mode}, "stages": []}), encoding="utf-8")
    (metadata / "run_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    table_path = root / "04_Tables" / "TABLE_CATALOGUE.csv"
    table_path.parent.mkdir()
    with table_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("schema_name", "object_name", "temporal_type_desc", "is_memory_optimized", "inferred_category"))
        writer.writeheader()
        writer.writerow({"schema_name": "dbo", "object_name": "T" + run_id, "temporal_type_desc": "NON_TEMPORAL_TABLE", "is_memory_optimized": "0", "inferred_category": "UNKNOWN"})
    report = root / "01_Executive_Summary" / "MSSQL_EXECUTIVE_SUMMARY.md"
    report.parent.mkdir()
    report.write_text("# Full evidence\n\nEvery line remains available.\n", encoding="utf-8")
    checklist = root / "99_Git_Handoff" / "SAFE_TO_COMMIT_CHECKLIST.md"
    checklist.parent.mkdir()
    checklist.write_text("# Checklist\n\n- PASS\n", encoding="utf-8")
    sql = root / "09_Stored_Procedures" / "definition.sql"
    sql.parent.mkdir()
    sql.write_text("\n".join(f"SELECT {index};" for index in range(120)), encoding="utf-8")
    return root


class WebAppTests(unittest.TestCase):
    def make_app(self, base: Path):
        settings = Settings(server="sql01", databases=("School",), output_root=base / "output", git_export_root=base / "git_export", web_auto_open_browser=False)
        return create_app(settings=settings, testing=True)

    @staticmethod
    def csrf(client) -> str:
        client.get("/")
        with client.session_transaction() as session:
            return session["csrf_token"]

    def test_main_help_and_default_launcher_wiring(self) -> None:
        completed = subprocess.run([sys.executable, str(Path(launcher.__file__).resolve()), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Read-only MSSQL documentation dashboard", completed.stdout)
        with patch("mssql_database_documenter.web.app.run_web", return_value=0) as run_web:
            self.assertEqual(launcher.main([]), 0)
            run_web.assert_called_once()

    def test_operator_guide_has_required_safe_sequence(self) -> None:
        guide = (Path(launcher.__file__).resolve().parent / "OPERATOR_RUN_GUIDE.md").read_text(encoding="utf-8")
        positions = [guide.index(label) for label in ("Dry Run", "Test Connection", "Metadata", "Metadata + Logic", "Safe Profile", "Create Git export")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Run A and Run B, plus optional Run C", guide)
        self.assertIn("do not expose it to a network interface", guide)

    def test_html_feature_checklist_is_fully_approved(self) -> None:
        checklist = (Path(launcher.__file__).resolve().parent / "HTML_FEATURE_CHECKLIST.md").read_text(encoding="utf-8")
        self.assertNotIn("- [ ]", checklist)
        for heading in ("Dashboard", "File browser", "Rendering", "Execution", "Compare"):
            self.assertIn(f"## {heading}", checklist)
        self.assertIn("Overall result: **PASS**", checklist)

    def test_import_has_no_output_or_git_export_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(launcher.__file__).resolve().parent
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join((str(project_root), str(project_root / "src")))
            completed = subprocess.run(
                [sys.executable, "-c", "import main; import mssql_database_documenter.fullrun"],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse((Path(directory) / "output").exists())
            self.assertFalse((Path(directory) / "git_export").exists())

    def test_all_top_level_command_routes_and_windows_launchers(self) -> None:
        with patch("mssql_database_documenter.web.app.run_web", return_value=0) as run_web:
            self.assertEqual(launcher.main(["web", "--no-browser"]), 0)
            run_web.assert_called_once_with(Path(".env"), auto_open=False)
        with patch("mssql_database_documenter.cli.main", return_value=0) as cli_main:
            self.assertEqual(launcher.main(["test-connection"]), 0)
            cli_main.assert_called_once_with(["--env-file", ".env", "test-connection"])
        for mode in ("metadata", "metadata+logic", "safe-profile", "full-readonly"):
            with self.subTest(mode=mode), patch("mssql_database_documenter.cli.main", return_value=0) as cli_main:
                self.assertEqual(launcher.main(["cli", "--mode", mode]), 0)
                cli_main.assert_called_once_with(["--env-file", ".env", "--mode", mode, "all"])
        for name, command in (("run_dashboard.bat", "main.py web"), ("run_metadata.bat", "main.py cli --mode metadata")):
            source = (Path(launcher.__file__).resolve().parent / name).read_text(encoding="utf-8")
            self.assertIn('if exist ".venv\\Scripts\\python.exe"', source)
            self.assertIn('set "PYTHON_EXE=python"', source)
            self.assertIn(command, source)
            self.assertIn("exit /b %EXIT_CODE%", source)
            self.assertNotIn("password", source.casefold())

    def test_app_is_lazy_loopback_only_and_has_security_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            app = self.make_app(base)
            self.assertFalse((base / "output").exists())
            self.assertFalse((base / "git_export").exists())
            response = app.test_client().get("/")
            self.assertEqual(response.status_code, 200)
            for label in (b"Dry Run", b"Test Connection", b"Metadata + Logic", b"Safe Profile", b"Full Read-Only", b"Generate Reports", b"Create Git export", b"Job ID", b"Elapsed"):
                self.assertIn(label, response.data)
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin")
            self.assertNotIn(b"https://", response.data)
            self.assertNotIn(b"http://", response.data)
            self.assertFalse((base / "output").exists())
        with self.assertRaises(ConfigurationError):
            create_app(settings=Settings(web_host="0.0.0.0"), testing=True)

    def test_host_origin_routes_and_secret_sanitization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            settings = Settings(server="private-sql", databases=("School",), trusted_connection=False, username="reader-user", password="top-secret", output_root=base / "output", git_export_root=base / "git")
            app = create_app(settings=settings, testing=True)
            client = app.test_client()
            dashboard = client.get("/")
            self.assertEqual(dashboard.status_code, 200)
            self.assertNotIn(b"private-sql", dashboard.data)
            self.assertNotIn(b"reader-user", dashboard.data)
            self.assertNotIn(b"top-secret", dashboard.data)
            self.assertEqual(client.get("/", headers={"Host": "attacker.example"}).status_code, 400)
            token = self.csrf(client)
            cross_origin = client.post(
                "/api/jobs/dry-run",
                json={},
                headers={"X-CSRF-Token": token, "Origin": "http://attacker.example"},
            )
            self.assertEqual(cross_origin.status_code, 403)
            for route in ("/", "/browser?root=output", "/compare", "/help"):
                with self.subTest(route=route):
                    self.assertEqual(client.get(route).status_code, 200)
            help_page = client.get("/help")
            for label in (b"What this project does", b"Why the steps are gradual", b"Output evidence", b"Safety model", b"Troubleshooting", b"Evidence labels"):
                self.assertIn(label, help_page.data)
            dashboard = client.get("/")
            for label in (b"Use these steps in order", b"What do these settings mean?", b"Action explanations", b"When is a run ready to export?", b"Open the full help guide"):
                self.assertIn(label, dashboard.data)
            comparison_page = client.get("/compare")
            for label in (b"Run A", b"Run B", b"Run C", b"Changed only", b"Object type", b"Schema", b"Severity", b"Database", b"Warnings/errors only", b"Run A</th>", b"A ", b"Numeric values/deltas", b"Definition comparisons"):
                self.assertIn(label, comparison_page.data)
            self.assertIn(b'id="compare-pager"', comparison_page.data)
            self.assertIn(b'class="sidebar"', comparison_page.data)
            for route in ("/api/shell", "/api/sql", "/api/eval", "/api/python"):
                with self.subTest(route=route):
                    self.assertEqual(client.post(route, headers={"X-CSRF-Token": token}).status_code, 404)

    def test_csrf_action_allowlist_invalid_database_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(Path(directory))
            client = app.test_client()
            self.assertEqual(client.post("/api/jobs/dry-run", json={}).status_code, 403)
            token = self.csrf(client)
            headers = {"X-CSRF-Token": token}
            self.assertEqual(client.post("/api/jobs/arbitrary-shell", json={}, headers=headers).status_code, 400)
            self.assertEqual(client.post("/api/jobs/metadata", json={"database": "NotAllowed"}, headers=headers).status_code, 400)
            response = client.post("/api/jobs/dry-run", json={"database": "School"}, headers=headers)
            self.assertEqual(response.status_code, 202)
            job = app.extensions["documenter_jobs"].wait(response.get_json()["id"])
            self.assertEqual(job.status, "COMPLETED")
            self.assertGreater(job.result["validated_query_count"], 0)
            self.assertFalse((Path(directory) / "output").exists())

    def test_console_connection_check_creates_no_runtime_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            env_file = base / ".env"
            output_root = base / "runtime-output"
            git_root = base / "runtime-git"
            env_file.write_text(
                f"MSSQL_SERVER=sql01\nMSSQL_DATABASE=School\nOUTPUT_ROOT={output_root}\nGIT_EXPORT_ROOT={git_root}\n",
                encoding="utf-8",
            )
            cursor = MagicMock()
            cursor.description = [("value",)]
            cursor.fetchall.return_value = [(1,)]
            connection = MagicMock()
            connection.cursor.return_value = cursor
            context = MagicMock()
            context.__enter__.return_value = connection
            context.__exit__.return_value = False
            with patch("mssql_database_documenter.connection.connect", return_value=context), patch("sys.stdout"):
                self.assertEqual(launcher.main(["--env-file", str(env_file), "test-connection"]), 0)
            self.assertFalse(output_root.exists())
            self.assertFalse(git_root.exists())

    def test_browser_raw_access_traversal_and_run_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = write_run(base / "output", "1")
            app = self.make_app(base)
            client = app.test_client()
            self.assertEqual(client.get("/browser?root=output").status_code, 200)
            browser_page = client.get("/browser?root=output&path=School/run_1")
            self.assertIn(b"Database", browser_page.data)
            self.assertIn(b"run_1", browser_page.data)
            self.assertIn(b"Git Export", browser_page.data)
            self.assertEqual(client.get("/file?root=output&path=../secret").status_code, 403)
            relative = (run / "01_Executive_Summary" / "MSSQL_EXECUTIVE_SUMMARY.md").relative_to(base / "output").as_posix()
            raw = client.get("/raw", query_string={"root": "output", "path": relative})
            self.assertEqual(raw.status_code, 200)
            self.assertIn(b"Every line remains available", raw.data)
            raw.close()
            sql_relative = (run / "09_Stored_Procedures" / "definition.sql").relative_to(base / "output").as_posix()
            sql_page = client.get("/file", query_string={"root": "output", "path": sql_relative, "per_page": 50})
            self.assertIn(b"Copy full SQL", sql_page.data)
            self.assertIn(b"Open raw", sql_page.data)
            self.assertIn(b"Download", sql_page.data)
            self.assertIn(b"Next", sql_page.data)
            runs = client.get("/api/runs").get_json()["runs"]
            self.assertEqual(runs[0]["run_id"], "1")
            detail = client.get("/run", query_string={"ref": runs[0]["ref"]})
            self.assertIn(b"Registry path", detail.data)
            self.assertIn(b"Errors", detail.data)
            self.assertIn(b"Warnings", detail.data)

    def test_two_run_compare_and_explicit_git_export_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            write_run(base / "output", "1")
            write_run(base / "output", "2")
            app = self.make_app(base)
            client = app.test_client()
            token = self.csrf(client)
            headers = {"X-CSRF-Token": token}
            refs = [item["ref"] for item in client.get("/api/runs").get_json()["runs"]]
            compared = client.post("/api/compare", json={"runs": refs, "export": False}, headers=headers)
            self.assertEqual(compared.status_code, 200)
            payload = compared.get_json()
            self.assertIsNone(payload["exports"])
            rows = client.get(f"/api/compare/{payload['id']}?category=tables").get_json()
            self.assertEqual(rows["total"], 2)
            self.assertFalse((base / "output" / "comparisons").exists())

            exported = client.post("/api/git-export", json={"run_ref": refs[0]}, headers=headers)
            self.assertEqual(exported.status_code, 202)
            job = app.extensions["documenter_jobs"].wait(exported.get_json()["id"])
            self.assertEqual(job.status, "COMPLETED")
            self.assertTrue((base / "git_export").is_dir())
            git_page = client.get("/browser?root=git_export")
            self.assertIn(b"SANITIZED GIT EXPORT", git_page.data)
            dashboard = client.get("/")
            self.assertIn(b"<strong>2</strong><span>recent indexed runs</span>", dashboard.data)

    def test_three_run_comparison_filters_raw_metadata_and_explicit_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for run_id in ("1", "2", "3"):
                write_run(base / "output", run_id)
            app = self.make_app(base)
            client = app.test_client()
            token = self.csrf(client)
            headers = {"X-CSRF-Token": token}
            refs = [item["ref"] for item in client.get("/api/runs").get_json()["runs"]]
            response = client.post("/api/compare", json={"runs": refs, "export": False}, headers=headers)
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertIn("category_metadata", payload)
            self.assertIn("does not infer cause", payload["semantic_note"])
            comparison_id = payload["id"]
            dbo = client.get(f"/api/compare/{comparison_id}?category=tables&schema=dbo").get_json()
            self.assertEqual(dbo["total"], 3)
            self.assertEqual(client.get(f"/api/compare/{comparison_id}?category=tables&schema=missing").get_json()["total"], 0)
            self.assertGreaterEqual(client.get(f"/api/compare/{comparison_id}?category=tables&status=ADDED").get_json()["total"], 1)
            self.assertEqual(client.get(f"/api/compare/{comparison_id}?category=tables&database=Other").get_json()["total"], 0)
            exported = client.post("/api/compare", json={"runs": refs, "export": True}, headers=headers).get_json()["exports"]
            self.assertEqual(set(exported), {"html", "csv", "json"})
            self.assertTrue(all(Path(path).is_file() for path in exported.values()))


if __name__ == "__main__":
    unittest.main()
