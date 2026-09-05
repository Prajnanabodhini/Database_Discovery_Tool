import unittest

from mssql_database_documenter.config import Settings
from mssql_database_documenter.connection import build_connection_string


class ConnectionStringTests(unittest.TestCase):
    def test_read_only_intent_and_trusted_auth(self) -> None:
        settings = Settings(server="sql01", databases=("One",))
        value = build_connection_string(settings, "One")
        self.assertIn("ApplicationIntent=ReadOnly", value)
        self.assertIn("Trusted_Connection=yes", value)
        self.assertNotIn("PWD=", value)

    def test_sql_auth_escapes_braces(self) -> None:
        settings = Settings(
            server="sql01",
            databases=("One",),
            trusted_connection=False,
            username="reader",
            password="a}b",
        )
        value = build_connection_string(settings, "One")
        self.assertIn("UID={reader}", value)
        self.assertIn("PWD={a}}b}", value)


if __name__ == "__main__":
    unittest.main()

