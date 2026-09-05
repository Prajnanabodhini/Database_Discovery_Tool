import unittest

from mssql_database_documenter.queries import QUERIES
from mssql_database_documenter.safety import ReadOnlyCursor, UnsafeSqlError, validate_read_only_sql


class FakeCursor:
    def __init__(self) -> None:
        self.executed = False

    def execute(self, sql: str, *parameters: object) -> str:
        self.executed = True
        return sql

    def dangerous_extension(self) -> None:
        self.executed = True


class SafetyTests(unittest.TestCase):
    def test_all_registered_queries_are_safe(self) -> None:
        for query in QUERIES:
            self.assertEqual(validate_read_only_sql(query.sql), query.sql)

    def test_allows_select_and_cte(self) -> None:
        validate_read_only_sql("SELECT name FROM sys.tables")
        validate_read_only_sql("WITH x AS (SELECT 1 AS n) SELECT n FROM x;")

    def test_forbidden_operations_are_rejected(self) -> None:
        unsafe = (
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET x = 1",
            "DELETE FROM t",
            "MERGE t USING s ON 1=1 WHEN MATCHED THEN UPDATE SET x=1;",
            "CREATE TABLE t (x int)",
            "DROP TABLE t",
            "EXEC dbo.DoWork",
            "DBCC CHECKDB",
            "SELECT * INTO copied FROM source",
            "SELECT NEXT VALUE FOR dbo.sequence",
            "SELECT * FROM OPENQUERY(linked, 'SELECT 1')",
            "SELECT 1; SELECT 2",
        )
        for sql in unsafe:
            with self.subTest(sql=sql), self.assertRaises(UnsafeSqlError):
                validate_read_only_sql(sql)

    def test_forbidden_words_in_literals_and_identifiers_are_harmless(self) -> None:
        validate_read_only_sql("SELECT 'delete' AS [drop]")

    def test_unterminated_content_is_rejected(self) -> None:
        for sql in ("SELECT 'x", "SELECT [x", "SELECT 1 /* x"):
            with self.subTest(sql=sql), self.assertRaises(UnsafeSqlError):
                validate_read_only_sql(sql)

    def test_cursor_revalidates_at_execution_boundary(self) -> None:
        fake = FakeCursor()
        cursor = ReadOnlyCursor(fake)
        with self.assertRaises(UnsafeSqlError):
            cursor.execute("DELETE FROM important_table")
        self.assertFalse(fake.executed)

    def test_executemany_is_never_available(self) -> None:
        with self.assertRaises(UnsafeSqlError):
            ReadOnlyCursor(FakeCursor()).executemany("SELECT 1", [])

    def test_unknown_cursor_capabilities_are_fail_closed(self) -> None:
        with self.assertRaises(UnsafeSqlError):
            ReadOnlyCursor(FakeCursor()).dangerous_extension()



if __name__ == "__main__":
    unittest.main()
