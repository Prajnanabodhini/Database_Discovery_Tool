import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from mssql_database_documenter.config import Settings
from mssql_database_documenter.contracts import DISCOVERY_CAPABILITY_MATRIX, EXTRA_OUTPUTS
from mssql_database_documenter.fullrun import SequentialRun
from mssql_database_documenter.lineage.agent import RAW_COMMAND_FIELD, analyze_agent_steps
from mssql_database_documenter.programmable_queries import SQL_AGENT_QUERY
from mssql_database_documenter.safety import validate_read_only_sql


FAKE_SECRET = "FakeSecret123!"


def _step(command: str, subsystem: str = "TSQL", step_id: int = 1) -> dict[str, object]:
    return {
        "server_name": "[SANITIZED]",
        "job_name": "Nightly School Load",
        "job_enabled": True,
        "description": "fixture",
        "step_id": step_id,
        "step_name": f"step-{step_id}",
        "subsystem": subsystem,
        RAW_COMMAND_FIELD: command,
        "database_name": "SchoolERP",
        "schedule_name": "Nightly",
    }


class SqlAgentLineageTests(unittest.TestCase):
    def test_agent_query_remains_select_only_and_raw_command_is_internal(self) -> None:
        validate_read_only_sql(SQL_AGENT_QUERY.sql)
        self.assertIn("js.command AS command_text_internal", SQL_AGENT_QUERY.sql)

    def test_exec_is_classified_as_a_static_call(self) -> None:
        jobs, references, _ = analyze_agent_steps([_step("EXEC dbo.LoadStudents")])
        call = next(row for row in references if row["operation"] == "CALL")
        self.assertEqual((call["target_schema"], call["target_object"]), ("dbo", "LoadStudents"))
        self.assertEqual(call["evidence_class"], "INFERENCE")
        self.assertNotIn(RAW_COMMAND_FIELD, jobs[0])

    def test_insert_select_produces_read_and_write_edges(self) -> None:
        jobs, references, edges = analyze_agent_steps(
            [_step("INSERT INTO dbo.Target SELECT * FROM dbo.Source")]
        )
        self.assertEqual({row["operation"] for row in references}, {"READ", "WRITE"})
        self.assertEqual(
            {(row["operation"], row["target_object"]) for row in references},
            {("READ", "Source"), ("WRITE", "Target")},
        )
        self.assertEqual({row["operation"] for row in edges}, {"READ", "WRITE"})
        self.assertEqual(jobs[0]["command_text_sanitized"], "INSERT INTO dbo.Target SELECT * FROM dbo.Source")

    def test_three_part_name_is_cross_database_inference(self) -> None:
        _, references, _ = analyze_agent_steps(
            [_step("SELECT StudentId FROM Archive.dbo.Students")]
        )
        row = references[0]
        self.assertEqual(row["reference_kind"], "THREE_PART")
        self.assertEqual(row["target_database"], "Archive")
        self.assertTrue(row["external_reference"])

    def test_external_tsql_construct_is_opaque_and_does_not_leak_arguments(self) -> None:
        command = "SELECT * FROM OPENQUERY([PrivateLinkedServer], 'SELECT * FROM SecretDb.dbo.People')"
        jobs, references, edges = analyze_agent_steps([_step(command)])
        external = next(row for row in references if row["reference_kind"] == "OPENQUERY")
        self.assertTrue(external["external_reference"])
        self.assertEqual(external["target_server"], "[STATIC_TEXT_REDACTED]")
        persisted = json.dumps((jobs, references, edges))
        self.assertNotIn("PrivateLinkedServer", persisted)
        self.assertNotIn("SecretDb", persisted)
        self.assertEqual(jobs[0]["command_text_sanitized"], "")

    def test_dynamic_sql_is_opaque_and_its_text_is_not_persistable(self) -> None:
        command = "DECLARE @sql nvarchar(max) = 'SELECT * FROM dbo.Private'; EXEC sys.sp_executesql @sql"
        jobs, references, edges = analyze_agent_steps([_step(command)])
        self.assertEqual(jobs[0]["command_classification"], "DYNAMIC_TSQL_OPAQUE")
        self.assertEqual(jobs[0]["command_text_sanitized"], "")
        self.assertTrue(any(row["reference_kind"] == "DYNAMIC_SQL" for row in references))
        self.assertTrue(any(row["dynamic_sql_opaque"] for row in edges))
        self.assertNotIn("Private", json.dumps((jobs, references, edges)))

    def test_powershell_fake_secret_never_leaves_analyzer(self) -> None:
        command = f"powershell.exe ./load.ps1 -Password '{FAKE_SECRET}' -Server private-host"
        jobs, references, edges = analyze_agent_steps([_step(command, "PowerShell")])
        persisted = json.dumps((jobs, references, edges))
        self.assertNotIn(FAKE_SECRET, persisted)
        self.assertNotIn("load.ps1", persisted)
        self.assertEqual(jobs[0]["command_text_sanitized"], "")
        self.assertEqual(jobs[0]["command_classification"], "POWERSHELL_OPAQUE")
        self.assertEqual(len(jobs[0]["command_sha256"]), 64)
        self.assertTrue(references[0]["external_reference"])

    def test_cmdexec_and_ssis_are_opaque_external_invocations(self) -> None:
        rows = [
            _step("cmd.exe /c private-loader.cmd --token=do-not-store", "CmdExec", 1),
            _step('SSIS /FILE "C:\\private\\SchoolLoad.dtsx"', "SSIS", 2),
        ]
        jobs, references, edges = analyze_agent_steps(rows)
        persisted = json.dumps((jobs, references, edges))
        self.assertNotIn("private-loader", persisted)
        self.assertNotIn("SchoolLoad.dtsx", persisted)
        self.assertEqual({row["command_classification"] for row in jobs}, {"CMDEXEC_OPAQUE", "SSIS_OPAQUE"})
        self.assertEqual({row["reference_kind"] for row in references}, {"EXTERNAL_INVOCATION", "SSIS_PACKAGE"})
        self.assertTrue(all(row["classification"] == "OPAQUE_EXTERNAL_STEP" for row in edges))

    def test_prompt_stage_persists_safe_artifacts_and_merges_edges(self) -> None:
        fixtures = [
            _step("INSERT INTO dbo.Target SELECT * FROM Archive.dbo.Source", "TSQL", 1),
            _step(f"powershell.exe ./load.ps1 -Password '{FAKE_SECRET}'", "PowerShell", 2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            run = SequentialRun(
                Settings(server="sql01", databases=("SchoolERP",), output_root=Path(directory) / "output"),
                "SchoolERP",
            )
            run.fetch = MagicMock(side_effect=lambda query, **_: fixtures if query is SQL_AGENT_QUERY else [])
            run.prompt05_programmable()
            self.assertNotIn(RAW_COMMAND_FIELD, json.dumps(run.data))
            for name in (
                "SQL_AGENT_JOB_CATALOGUE.csv",
                "SQL_AGENT_STEP_REFERENCES.csv",
                "SQL_AGENT_PIPELINE_EDGES.csv",
            ):
                text = run.artifact(name).read_text(encoding="utf-8-sig")
                self.assertNotIn(FAKE_SECRET, text)
                self.assertNotIn("load.ps1", text)
            self.assertTrue(run.data["sql_agent_step_references"])
            self.assertTrue(run.data["sql_agent_pipeline_edges"])

            run.data.update({"columns": [], "views": [], "procedures": [], "functions": [], "triggers": []})
            run.prompt11_lineage()
            run._pipelines()
            self.assertTrue(any(row["source_type"] == "SQL_AGENT_STEP" for row in run.data["lineage"]))
            self.assertTrue(any(row.get("job_name") == "Nightly School Load" for row in run.data["pipelines"]))
            with run.artifact("LINEAGE_EDGES.csv").open(encoding="utf-8-sig", newline="") as handle:
                headers = next(csv.reader(handle))
            self.assertIn("evidence_class", headers)

    def test_contract_advertises_both_agent_lineage_outputs(self) -> None:
        expected = {"SQL_AGENT_STEP_REFERENCES.csv", "SQL_AGENT_PIPELINE_EDGES.csv"}
        self.assertTrue(expected.issubset(EXTRA_OUTPUTS))
        self.assertTrue(expected.issubset(DISCOVERY_CAPABILITY_MATRIX["agent_jobs"]))

    def test_analyzer_source_contains_no_execution_primitives(self) -> None:
        source = (Path(__file__).parents[1] / "src" / "mssql_database_documenter" / "lineage" / "agent.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "Popen(", "shell=True", "pyodbc"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
