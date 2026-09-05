from pathlib import Path
import unittest

from mssql_database_documenter.config import ConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def test_v3_env_example_is_complete_parseable_and_non_secret(self) -> None:
        example = Path(__file__).parents[1] / ".env.example"
        source = example.read_text(encoding="utf-8")
        settings = Settings.from_environment(env={}, dotenv_path=example)
        self.assertEqual(settings.server, "localhost")
        self.assertEqual(settings.databases, ("DatabaseName",))
        self.assertEqual(settings.profile_sample_rows, 100)
        self.assertEqual(settings.profile_exact_row_count_threshold, 100_000)
        self.assertEqual(settings.web_host, "127.0.0.1")
        self.assertEqual(settings.max_concurrent_discovery_jobs, 1)
        for line in source.splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            if key in {"MSSQL_TRUSTED_CONNECTION", "MSSQL_ENCRYPT", "MSSQL_TRUST_SERVER_CERTIFICATE", "PROFILE_INCLUDE_SAMPLE_DATA", "PROFILE_MASK_SENSITIVE_DATA", "PROFILE_EXACT_ROW_COUNTS", "PROFILE_DISTINCT_VALUES", "DISCOVER_SQL_AGENT_JOBS", "SANITIZE_SERVER_NAME", "WEB_AUTO_OPEN_BROWSER", "ENABLE_THREE_RUN_COMPARISON"}:
                self.assertIn(value, {"true", "false", "yes", "no"})
        self.assertNotIn("password=", source.casefold().replace("# mssql_password=", ""))

    def test_single_database_configuration(self) -> None:
        settings = Settings.from_environment(
            env={"MSSQL_DATABASE": "School", "MSSQL_SERVER": "sql01"},
            dotenv_path=None,
        )
        self.assertEqual(settings.databases, ("School",))

    def test_multi_database_configuration(self) -> None:
        settings = Settings.from_environment(
            env={"MSSQL_DATABASES": "One, Two"}, dotenv_path=None
        )
        self.assertEqual(settings.databases, ("One", "Two"))

    def test_prompt_v3_defaults_and_case_insensitive_booleans(self) -> None:
        settings = Settings.from_environment(
            env={
                "MSSQL_ENCRYPT": "NO",
                "MSSQL_TRUST_SERVER_CERTIFICATE": "YeS",
                "PROFILE_INCLUDE_SAMPLE_DATA": "TrUe",
            },
            dotenv_path=None,
        )
        self.assertFalse(settings.encrypt)
        self.assertTrue(settings.trust_server_certificate)
        self.assertTrue(settings.profile_include_sample_data)
        self.assertEqual(settings.profile_sample_rows, 100)
        self.assertEqual(settings.profile_max_distinct_values, 50)

    def test_exact_count_has_separate_safe_threshold_and_explicit_override(self) -> None:
        default = Settings.from_environment(env={}, dotenv_path=None)
        overridden = Settings.from_environment(
            env={"PROFILE_EXACT_ROW_COUNT_THRESHOLD": "250000"}, dotenv_path=None
        )
        self.assertEqual(default.profile_exact_row_count_threshold, 100_000)
        self.assertEqual(overridden.profile_exact_row_count_threshold, 250_000)

    def test_rejects_single_and_multi_database_together(self) -> None:
        with self.assertRaises(ConfigurationError):
            Settings.from_environment(
                env={"MSSQL_DATABASE": "One", "MSSQL_DATABASES": "Two"},
                dotenv_path=None,
            )

    def test_sql_auth_requires_both_credentials(self) -> None:
        settings = Settings.from_environment(
            env={
                "MSSQL_SERVER": "sql01",
                "MSSQL_DATABASE": "One",
                "MSSQL_TRUSTED_CONNECTION": "false",
                "MSSQL_USERNAME": "reader",
            },
            dotenv_path=None,
        )
        with self.assertRaises(ConfigurationError):
            settings.validate_for_connection()

    def test_sanitized_configuration_hides_secrets_and_server(self) -> None:
        settings = Settings(
            server="secret-server", username="reader", password="do-not-show"
        )
        sanitized = settings.sanitized()
        self.assertEqual(sanitized["server"], "[SANITIZED]")
        self.assertEqual(sanitized["username"], "[REDACTED]")
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertNotIn("do-not-show", str(sanitized))

    def test_dotenv_does_not_override_explicit_environment(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env"
            path.write_text("MSSQL_SERVER=from-file\n", encoding="utf-8")
            settings = Settings.from_environment(
                env={"MSSQL_SERVER": "from-env"}, dotenv_path=path
            )
        self.assertEqual(settings.server, "from-env")

    def test_mode_override_is_validated(self) -> None:
        settings = Settings().with_mode_override("safe-profile")
        self.assertEqual(settings.discovery_mode, "safe-profile")
        with self.assertRaises(ConfigurationError):
            settings.with_mode_override("unsafe")

    def test_web_configuration_is_loopback_and_single_job_only(self) -> None:
        Settings().validate_for_web()
        with self.assertRaises(ConfigurationError):
            Settings(web_host="0.0.0.0").validate_for_web()
        with self.assertRaises(ConfigurationError):
            Settings(max_concurrent_discovery_jobs=2).validate_for_web()
        with self.assertRaises(ConfigurationError):
            Settings(web_port=70000).validate_for_web()


if __name__ == "__main__":
    unittest.main()
