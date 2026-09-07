import csv
from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.config import Settings
from mssql_database_documenter.fullrun import (
    SequentialRun,
    _definition_references,
    _object_key,
    _static_column_references,
    _static_definition,
    _type_family,
)


class FullRunCharacterizationTests(unittest.TestCase):
    def make_run(self, directory: str) -> SequentialRun:
        return SequentialRun(
            Settings(output_root=Path(directory) / "output"),
            "SchoolERP",
        )

    def test_public_stage_compatibility_surface_is_stable(self) -> None:
        expected = {
            "prompt02_safety", "prompt03_connection", "prompt04_metadata",
            "prompt05_programmable", "prompt06_size_shape", "prompt07_profile",
            "prompt08_samples", "prompt09_sensitivity", "prompt10_relationships",
            "prompt11_lineage", "prompt12_external", "prompt13_classification",
            "prompt14_quality", "prompt15_outputs", "prompt16_safety_review",
            "prompt17_acceptance", "prompt18_comparison", "prompt19_required",
            "prompt20_environment", "prompt21_review", "run", "finalize",
            "resume_after_comparison",
        }
        self.assertTrue(expected.issubset(set(dir(SequentialRun))))

    def test_static_analysis_helper_semantics_are_characterized(self) -> None:
        definition = _static_definition({
            "definition": "SELECT s.Id, SUM(s.Amount) FROM dbo.Source AS s GROUP BY s.Id"
        })
        self.assertTrue(definition["definition_available"])
        self.assertFalse(definition["dynamic_sql_present"])
        self.assertFalse(definition["likely_write_logic"])
        refs = _definition_references(definition)
        self.assertIn(("READ", "dbo", "Source"), {
            (row["operation"], row["target_schema"], row["target_object"]) for row in refs
        })
        columns = _static_column_references(definition, {("dbo", "Source"): {"id", "amount"}})
        self.assertIn(("Amount", "AGGREGATED"), {
            (row["target_column"], row["lineage_type"]) for row in columns
        })
        self.assertEqual(_type_family("nvarchar"), "STRING")
        self.assertEqual(_object_key({"schema_name": "dbo", "object_name": "Student"}), "dbo.Student")

    def test_pipeline_evidence_rows_and_headers_are_characterized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = self.make_run(directory)
            run.data = {
                "views": [{"schema_name": "dbo", "object_name": "LoadView", "dynamic_sql_present": False}],
                "procedures": [], "functions": [], "triggers": [],
                "static_references": [
                    {"source_schema": "dbo", "source_object": "LoadView", "operation": "READ", "target_database": "SchoolERP", "target_schema": "dbo", "target_object": "Source"},
                    {"source_schema": "dbo", "source_object": "LoadView", "operation": "WRITE", "target_database": "SchoolERP", "target_schema": "dbo", "target_object": "Target"},
                ],
                "dependencies": [],
                "sql_agent_pipeline_edges": [{
                    "job_name": "Nightly", "step_id": 1, "step_name": "Load", "subsystem": "TSQL",
                    "origin": "SQL Agent job: Nightly", "source": "SchoolERP.dbo.Source",
                    "transformation": "Load", "destination": "SchoolERP.dbo.Target", "schedule": "Nightly",
                    "operation": "WRITE", "read_write_evidence": "STATIC TSQL TOKEN REFERENCE; NEVER EXECUTED",
                    "external_dependency": False, "classification": "POSSIBLE_PIPELINE",
                    "confidence": "MEDIUM", "evidence_class": "INFERENCE", "reference_kind": "TWO_PART",
                    "dynamic_sql_opaque": False,
                }],
            }
            run._pipelines()
            self.assertEqual(len(run.data["pipelines"]), 2)
            static = run.data["pipelines"][0]
            self.assertEqual(static["classification"], "LIKELY_PIPELINE")
            self.assertEqual(static["evidence_class"], "INFERENCE")
            agent = run.data["pipelines"][1]
            self.assertEqual(agent["origin"], "SQL Agent job: Nightly")
            with run.artifact("PIPELINE_CATALOGUE.csv").open(encoding="utf-8-sig", newline="") as handle:
                headers = next(csv.reader(handle))
            self.assertEqual(headers[:5], ["origin", "source", "transformation", "destination", "schedule"])
            self.assertIn("evidence_class", headers)

    def test_narrative_and_control_file_content_is_characterized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = self.make_run(directory)
            run.data = {
                "tables": [{"schema_name": "dbo", "object_name": "Student"}],
                "columns": [{"schema_name": "dbo", "object_name": "Student"}],
                "views": [], "procedures": [], "functions": [], "triggers": [],
                "foreign_keys": [], "inferred_relationships": [], "lineage": [],
                "risks": [], "pipelines": [], "sample_rows": {}, "column_profile": [],
            }
            run._narratives()
            run._write_control_files(final=False)
            metrics = run.artifact("DATABASE_SUMMARY_METRICS.json").read_text(encoding="utf-8")
            self.assertIn('"tables": 1', metrics)
            summary = run.artifact("MSSQL_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("contains 1 tables and 1 columns", summary)
            coverage = run.artifact("DISCOVERY_COVERAGE.md").read_text(encoding="utf-8")
            self.assertIn("Finalized: False", coverage)
            self.assertIn("No query/access errors were recorded", coverage)


if __name__ == "__main__":
    unittest.main()
