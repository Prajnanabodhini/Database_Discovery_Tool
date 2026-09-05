import unittest

from mssql_database_documenter.redaction import redact_text


class RedactionTests(unittest.TestCase):
    def test_redacts_connection_password(self) -> None:
        result = redact_text("SERVER=x;UID=user;PWD=hunter2;Encrypt=yes")
        self.assertNotIn("hunter2", result)
        self.assertIn("PWD=[REDACTED]", result)

    def test_redacts_token_assignment(self) -> None:
        result = redact_text("token=abc123 error")
        self.assertNotIn("abc123", result)

    def test_redacts_known_sensitive_values(self) -> None:
        result = redact_text(
            "Connection to secret-server failed for reader",
            sensitive_values=("secret-server", "reader"),
        )
        self.assertNotIn("secret-server", result)
        self.assertNotIn("reader", result)

    def test_redacts_escaped_server_from_exception_representation(self) -> None:
        result = redact_text(
            r"connection to HOST\\INSTANCE failed",
            sensitive_values=(r"HOST\INSTANCE",),
        )
        self.assertNotIn("HOST", result)
        self.assertNotIn("INSTANCE", result)


if __name__ == "__main__":
    unittest.main()
