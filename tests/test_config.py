from pathlib import Path
import importlib.metadata
import tomllib
import unittest

from mssql_database_documenter import __version__
from mssql_database_documenter.config import ConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def test_package_and_project_versions_are_one_v31_identity(self) -> None:
        project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(__version__, "0.3.1")
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(importlib.metadata.version("mssql-database-documenter"), __version__)

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
        self.assertEqual(settings.git_export_sample_policy, "exclude")
        self.assertEqual(settings.git_export_profile_value_policy, "mask_unknown_text")
        self.assertTrue(settings.sample_tables)
        self.assertTrue(settings.sample_views)
        self.assertTrue(settings.sample_large_tables)
        self.assertEqual(settings.sample_row_limit, 100)
        self.assertEqual(settings.full_readonly_sample_row_limit, 500)
        self.assertEqual(settings.full_readonly_profile_threshold, 5_000_000)
        self.assertEqual(settings.full_readonly_exact_count_threshold, 500_000)
        self.assertEqual(settings.full_readonly_relationship_threshold, 5_000_000)
        self.assertEqual(settings.full_readonly_low_cardinality_limit, 200)
        self.assertTrue(settings.full_readonly_extended_validation)
        for line in source.splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            if key in {"MSSQL_TRUSTED_CONNECTION", "MSSQL_ENCRYPT", "MSSQL_TRUST_SERVER_CERTIFICATE", "SAMPLE_TABLES", "SAMPLE_VIEWS", "SAMPLE_LARGE_TABLES", "PROFILE_INCLUDE_SAMPLE_DATA", "PROFILE_MASK_SENSITIVE_DATA", "PROFILE_EXACT_ROW_COUNTS", "PROFILE_DISTINCT_VALUES", "FULL_READONLY_EXTENDED_VALIDATION", "DISCOVER_SQL_AGENT_JOBS", "DISCOVER_SECURITY_METADATA", "SANITIZE_SERVER_NAME", "WEB_AUTO_OPEN_BROWSER", "ENABLE_THREE_RUN_COMPARISON"}:
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

    def test_git_export_sample_policy_is_fail_closed(self) -> None:
        masked = Settings.from_environment(env={"GIT_EXPORT_SAMPLE_POLICY": "MASKED_ONLY"}, dotenv_path=None)
        self.assertEqual(masked.git_export_sample_policy, "masked_only")
        with self.assertRaises(ConfigurationError):
            Settings.from_environment(env={"GIT_EXPORT_SAMPLE_POLICY": "raw"}, dotenv_path=None)

    def test_git_export_profile_value_policy_defaults_secure_and_rejects_raw(self) -> None:
        default = Settings.from_environment(env={}, dotenv_path=None)
        aggregate = Settings.from_environment(
            env={"GIT_EXPORT_PROFILE_VALUE_POLICY": "AGGREGATE_ONLY"}, dotenv_path=None,
        )
        self.assertEqual(default.git_export_profile_value_policy, "mask_unknown_text")
        self.assertEqual(aggregate.git_export_profile_value_policy, "aggregate_only")
        with self.assertRaises(ConfigurationError):
            Settings.from_environment(
                env={"GIT_EXPORT_PROFILE_VALUE_POLICY": "raw"}, dotenv_path=None,
            )

    def test_canonical_sampling_settings_and_legacy_fallback(self) -> None:
        canonical = Settings.from_environment(
            env={
                "SAMPLE_TABLES": "false", "SAMPLE_VIEWS": "true",
                "SAMPLE_LARGE_TABLES": "false", "SAMPLE_ROW_LIMIT": "17",
                "PROFILE_SAMPLE_ROWS": "999", "PROFILE_INCLUDE_SAMPLE_DATA": "false",
            },
            dotenv_path=None,
        )
        self.assertFalse(canonical.sample_tables)
        self.assertTrue(canonical.sample_views)
        self.assertFalse(canonical.sample_large_tables)
        self.assertEqual(canonical.sample_row_limit, 17)
        self.assertEqual(canonical.profile_sample_rows, 17)
        self.assertTrue(canonical.profile_include_sample_data)

        legacy = Settings.from_environment(
            env={"PROFILE_SAMPLE_ROWS": "12", "PROFILE_INCLUDE_SAMPLE_DATA": "false"},
            dotenv_path=None,
        )
        self.assertEqual(legacy.sample_row_limit, 12)
        self.assertFalse(legacy.sample_tables)
        self.assertFalse(legacy.sample_views)
        with self.assertRaises(ConfigurationError):
            Settings.from_environment(env={"SAMPLE_ROW_LIMIT": "0"}, dotenv_path=None)


if __name__ == "__main__":
    unittest.main()
