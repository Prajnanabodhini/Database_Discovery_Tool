from contextlib import redirect_stdout
from io import StringIO
import json
import unittest

from mssql_database_documenter.cli import main


class CliTests(unittest.TestCase):
    def test_dry_run_never_requires_or_attempts_connection(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--env-file", "missing.env", "dry-run"])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["connection_attempted"])
        self.assertTrue(all(item["status"] == "SAFE" for item in payload["queries"]))
        names = {item["name"] for item in payload["queries"]}
        self.assertIn("procedures", names)
        self.assertIn("sql_agent_jobs", names)


if __name__ == "__main__":
    unittest.main()
