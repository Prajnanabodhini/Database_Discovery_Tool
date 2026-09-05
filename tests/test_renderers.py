import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mssql_database_documenter.web.renderers import render_file


class RendererTests(unittest.TestCase):
    def test_large_csv_is_paginated_without_column_or_row_loss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=("id", "name", "note"))
                writer.writeheader()
                writer.writerows({"id": index, "name": f"row-{index:03d}", "note": "complete"} for index in range(250))
            page = render_file(path, page=3, per_page=100)
            self.assertEqual(page["headers"], ["id", "name", "note"])
            self.assertEqual(page["pagination"], {"page": 3, "per_page": 100, "total": 250, "start": 201, "end": 250})
            self.assertEqual(len(page["rows"]), 50)
            filtered = render_file(path, search="row-149", sort="id", descending=True)
            self.assertEqual(filtered["rows"][0]["id"], "149")
            self.assertEqual(len(path.read_text(encoding="utf-8-sig").splitlines()), 251)

    def test_markdown_json_sql_and_mermaid_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markdown_path = root / "report.md"
            markdown_path.write_text("# Heading\n\n| A |\n|---|\n| value |\n\n!!! note\n    Read-only callout.\n\n<script>alert(1)</script>", encoding="utf-8")
            original_digest = hashlib.sha256(markdown_path.read_bytes()).hexdigest()
            rendered_markdown = render_file(markdown_path)
            self.assertEqual(rendered_markdown["kind"], "markdown")
            self.assertIn("<h1>Heading</h1>", rendered_markdown["html"])
            self.assertNotIn("<script>", rendered_markdown["html"])
            self.assertIn('class="admonition note"', rendered_markdown["html"])
            self.assertEqual(hashlib.sha256(markdown_path.read_bytes()).hexdigest(), original_digest)

            json_path = root / "value.json"
            json_path.write_text(json.dumps({"a": [1, 2]}), encoding="utf-8")
            rendered_json = render_file(json_path)
            self.assertEqual(rendered_json["kind"], "json")
            self.assertEqual(rendered_json["json"]["a"], [1, 2])

            sql_path = root / "definition.sql"
            sql_path.write_text("SELECT 1;\nSELECT 2;", encoding="utf-8")
            rendered_sql = render_file(sql_path, page=2, per_page=1)
            self.assertEqual(rendered_sql["kind"], "sql")
            self.assertEqual(rendered_sql["lines"][0]["text"], "SELECT 2;")

            mermaid_path = root / "FULL_ER_DIAGRAM.md"
            mermaid_path.write_text("```mermaid\nerDiagram\n```", encoding="utf-8")
            self.assertEqual(render_file(mermaid_path)["kind"], "mermaid")

    def test_untrusted_html_is_text_and_paginated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outside.html"
            path.write_text("<script>x</script>\n<p>line two</p>", encoding="utf-8")
            rendered = render_file(path, page=1, per_page=1)
            self.assertEqual(rendered["kind"], "text")
            self.assertFalse(rendered["trusted"])
            self.assertEqual(rendered["pagination"]["total"], 2)

    def test_trusted_generated_html_keeps_report_structure_without_executable_markup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_folder = Path(directory) / "21_HTML_Report"
            report_folder.mkdir()
            path = report_folder / "report.html"
            path.write_text(
                "<!doctype html><html><head><style>body{color:red}</style><script>alert('head')</script></head>"
                "<body><main class='report'><section onclick='alert(1)'><h1>Readable report</h1>"
                "<table><tr><th>Item</th></tr><tr><td>Value</td></tr></table>"
                "<a href='javascript:alert(2)'>unsafe</a><script>alert('body')</script></section></main></body></html>",
                encoding="utf-8",
            )
            rendered = render_file(path)
            self.assertEqual(rendered["kind"], "html")
            self.assertTrue(rendered["trusted"])
            self.assertIn("<main", rendered["html"])
            self.assertIn("<h1>Readable report</h1>", rendered["html"])
            self.assertIn("<table>", rendered["html"])
            self.assertNotIn("&lt;html", rendered["html"])
            self.assertNotIn("<script", rendered["html"])
            self.assertNotIn("onclick", rendered["html"])
            self.assertNotIn("javascript:", rendered["html"])
            self.assertNotIn("alert(", rendered["html"])

    def test_large_structured_files_fall_back_to_complete_paginated_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.json"
            path.write_text('{"rows":[1,2,3]}\n', encoding="utf-8")
            with patch("mssql_database_documenter.web.renderers.MAX_FORMATTED_FILE_BYTES", 10):
                rendered = render_file(path, page=1, per_page=1)
            self.assertEqual(rendered["kind"], "text")
            self.assertEqual(rendered["pagination"]["total"], 1)
            self.assertIn("memory-bounded", rendered["notice"])

    def test_text_pagination_does_not_use_unbounded_read_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.txt"
            path.write_text("one\ntwo\nthree\n", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=AssertionError("unbounded read")):
                rendered = render_file(path, page=2, per_page=1)
            self.assertEqual(rendered["lines"], [{"number": 2, "text": "two"}])


if __name__ == "__main__":
    unittest.main()
