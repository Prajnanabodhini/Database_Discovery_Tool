import csv
import json
from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.comparison import (
    _read_rows,
    compare_rows,
    compare_run_paths,
    load_run,
    write_database_comparison,
)


def write_csv(root: Path, relative: str, rows: list[dict[str, object]]) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0]) if rows else ["status"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_run(base: Path, run_id: str, database: str, mode: str = "metadata+logic") -> Path:
    root = base / database / f"run_{run_id}"
    metadata = root / "00_Run_Metadata"
    metadata.mkdir(parents=True)
    summary = {
        "run_id": run_id,
        "database": database,
        "server_alias": "[SANITIZED]",
        "timestamp_utc": f"2026-01-0{run_id}T00:00:00+00:00",
        "mode": mode,
        "status": "COMPLETED",
        "tool_version": "0.3.0",
        "sql_server_version": "16.0",
        "sample_rows": 10,
        "exact_row_counts": False,
        "completed_stage_count": 20,
        "warning_error_count": 0,
    }
    (metadata / "run_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (metadata / "manifest.json").write_text(
        json.dumps({"run_id": run_id, "database": database, "tool_version": "0.3.0", "configuration": {"discovery_mode": mode}, "stages": []}),
        encoding="utf-8",
    )
    return root


class ComparisonTests(unittest.TestCase):
    def test_compare_rows_reports_unchanged_changed_and_added(self) -> None:
        rows = compare_rows(
            {
                "A": [{"schema": "dbo", "name": "same", "type": "int"}, {"schema": "dbo", "name": "changed", "type": "int"}],
                "B": [{"schema": "dbo", "name": "same", "type": "int"}, {"schema": "dbo", "name": "changed", "type": "bigint"}, {"schema": "dbo", "name": "only_b", "type": "int"}],
            },
            ("schema", "name"),
            ("type",),
        )
        statuses = {row["identity"]["name"]: row["status"] for row in rows}
        self.assertEqual(statuses, {"changed": "CHANGED", "only_b": "ADDED", "same": "UNCHANGED"})

    def test_two_run_comparison_reports_removed(self) -> None:
        rows = compare_rows(
            {"A": [{"schema": "dbo", "name": "removed", "type": "int"}], "B": []},
            ("schema", "name"),
            ("type",),
        )
        self.assertEqual(rows[0]["status"], "REMOVED")

    def test_three_run_timeline_numeric_deltas_and_definition_diff(self) -> None:
        rows = compare_rows(
            {
                "A": [{"name": "proc", "count": "100", "hash": "a", "definition": "SELECT 1"}],
                "B": [{"name": "proc", "count": "120", "hash": "b", "definition": "SELECT 2"}, {"name": "new", "count": "5", "hash": "x", "definition": "SELECT 3"}],
                "C": [{"name": "proc", "count": "100", "hash": "a", "definition": "SELECT 1"}, {"name": "new", "count": "5", "hash": "x", "definition": "SELECT 3"}],
            },
            ("name",),
            ("count", "hash"),
            ("count",),
            "definition",
        )
        by_name = {row["identity"]["name"]: row for row in rows}
        self.assertEqual(by_name["new"]["status"], "ADDED_IN_B")
        self.assertEqual(by_name["proc"]["status"], "REVERTED_TO_A")
        delta = by_name["proc"]["numeric_deltas"]["count"]
        self.assertEqual((delta["A"], delta["B"], delta["C"]), (100.0, 120.0, 100.0))
        self.assertEqual(delta["B_MINUS_A"], 20.0)
        self.assertEqual(delta["C_MINUS_B"], -20.0)
        self.assertEqual(delta["C_MINUS_A_PERCENT"], 0.0)
        self.assertIn("-SELECT 1", by_name["proc"]["definition_diffs"]["A_TO_B"])

    def test_all_required_three_run_timeline_patterns(self) -> None:
        rows = compare_rows(
            {
                "A": [{"name": "remove_b", "v": "1"}, {"name": "remove_c", "v": "1"}, {"name": "both", "v": "1"}, {"name": "revert", "v": "1"}],
                "B": [{"name": "remove_c", "v": "1"}, {"name": "both", "v": "2"}, {"name": "revert", "v": "2"}],
                "C": [{"name": "add_c", "v": "1"}, {"name": "both", "v": "3"}, {"name": "revert", "v": "1"}],
            },
            ("name",),
            ("v",),
        )
        by_name = {row["identity"]["name"]: row for row in rows}
        self.assertEqual(by_name["add_c"]["status"], "ADDED_IN_C")
        self.assertEqual(by_name["remove_b"]["status"], "REMOVED_IN_B")
        self.assertEqual(by_name["remove_c"]["status"], "REMOVED_IN_C")
        self.assertEqual(by_name["both"]["status"], "CHANGED_BOTH")
        self.assertEqual(by_name["revert"]["status"], "REVERTED_TO_A")
        self.assertEqual(by_name["both"]["legacy_status_alias"], "CHANGED_BOTH_INTERVALS")

    def test_normalized_keys_and_unavailable_evidence_are_not_misreported(self) -> None:
        normalized = compare_rows(
            {"A": [{"schema": " DBO ", "name": "T", "v": "1"}], "B": [{"schema": "dbo", "name": "t", "v": "1"}]},
            ("schema", "name"),
            ("v",),
        )
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["status"], "UNCHANGED")
        unavailable = compare_rows(
            {"A": [{"name": "T", "v": "1"}], "B": []},
            ("name",),
            ("v",),
            availability={"A": True, "B": False},
        )
        self.assertEqual(unavailable[0]["status"], "NOT_COMPARABLE")

    def test_manifested_runs_compare_and_export_without_merging_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            runs = {}
            for run_id, database, data_type in (("1", "A", "int"), ("2", "B", "bigint")):
                run = write_run(base, run_id, database)
                write_csv(run, "05_Columns/COLUMN_CATALOGUE.csv", [{"schema_name": "dbo", "object_name": "T", "column_name": "id", "data_type": data_type, "max_length": "4", "precision": "10", "scale": "0", "is_nullable": "0", "is_identity": "1", "is_computed": "0"}])
                runs[database] = run
            payload = write_database_comparison(base / "comparison", runs)
            self.assertTrue((base / "comparison" / "DATABASE_COMPARISON.html").is_file())
            self.assertTrue((base / "comparison" / "DATABASE_COMPARISON.csv").is_file())
            parsed = json.loads((base / "comparison" / "DATABASE_COMPARISON.json").read_text(encoding="utf-8"))
            self.assertEqual(set(parsed["runs"]), {"A", "B"})
            self.assertIn("Mixed databases", " ".join(payload["warnings"]))

    def test_procedure_hash_change_and_mixed_mode_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first = write_run(base, "1", "School", "metadata+logic")
            second = write_run(base, "2", "School", "full-readonly")
            write_csv(first, "09_Stored_Procedures/STORED_PROCEDURE_CATALOGUE.csv", [{"schema_name": "dbo", "object_name": "p", "definition_sha256": "old", "definition_sanitized": "SELECT 1"}])
            write_csv(second, "09_Stored_Procedures/STORED_PROCEDURE_CATALOGUE.csv", [{"schema_name": "dbo", "object_name": "p", "definition_sha256": "new", "definition_sanitized": "SELECT 2"}])
            metrics_a = first / "02_Server_Database" / "DATABASE_SUMMARY_METRICS.json"
            metrics_b = second / "02_Server_Database" / "DATABASE_SUMMARY_METRICS.json"
            metrics_a.parent.mkdir(parents=True); metrics_b.parent.mkdir(parents=True)
            metrics_a.write_text(json.dumps({"tables": 10}), encoding="utf-8")
            metrics_b.write_text(json.dumps({"tables": 15}), encoding="utf-8")
            result = compare_run_paths([load_run(first), load_run(second)])
            row = result["categories"]["procedures"]["rows"][0]
            self.assertEqual(row["status"], "CHANGED")
            self.assertIn("A_TO_B", row["definition_diffs"])
            combined = result["categories"]["definition_hashes"]["rows"][0]
            self.assertEqual(combined["status"], "CHANGED")
            summary = next(item for item in result["categories"]["database_summary"]["rows"] if item["identity"]["metric"] == "tables")
            self.assertEqual(summary["numeric_deltas"]["value"]["B_MINUS_A"], 5.0)
            self.assertIn("Discovery modes differ", " ".join(result["warnings"]))
            self.assertIn("does not infer cause", result["semantic_note"])

    def test_large_sanitized_definition_fields_are_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalogue.csv"
            value = "SELECT 1 -- sanitized\n" * 10_000
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=("definition_sanitized",))
                writer.writeheader()
                writer.writerow({"definition_sanitized": value})
            self.assertEqual(_read_rows(path)[0]["definition_sanitized"], value)


if __name__ == "__main__":
    unittest.main()
