from pathlib import Path
import tempfile
import unittest

from mssql_database_documenter.profiling.sensitivity import (
    classify_sensitivity,
    load_sensitivity_overrides,
)


class SensitivityClassificationTests(unittest.TestCase):
    def test_legacy_school_erp_names_are_pii(self) -> None:
        for name in (
            "StudNm", "FName", "MName", "FatherNm", "MobNo", "PhNo", "ContactNo",
            "Addr1", "ResAdd", "BDate", "BirthDt", "Aadhar", "PANNo",
        ):
            with self.subTest(name=name):
                result = classify_sensitivity(name)
                self.assertEqual(result.category, "PII")
                self.assertEqual(result.action, "PSEUDONYMIZE")
                self.assertEqual(result.confidence, "HIGH")
                self.assertEqual(result.evidence, "BUILTIN_LEGACY_COLUMN_NAME")

    def test_exact_override_precedes_pattern_and_builtin(self) -> None:
        source = """
[[rules]]
match = "pattern"
database = "School*"
schema = "dbo"
table = "Student*"
column = "*Name"
category = "Potentially Sensitive"
action = "PSEUDONYMIZE"
reason = "wide pattern"

[[rules]]
match = "exact"
database = "School"
schema = "dbo"
table = "Student"
column = "StudName"
category = "Non-sensitive"
action = "PRESERVE"
confidence = "HIGH"
reason = "approved identifier"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overrides.toml"
            path.write_text(source, encoding="utf-8")
            rules = load_sensitivity_overrides(path)
        result = classify_sensitivity(
            "StudName", database="School", schema="dbo", table="Student", overrides=rules
        )
        self.assertEqual(result.category, "Non-sensitive")
        self.assertEqual(result.action, "PRESERVE")
        self.assertEqual(result.evidence, "OVERRIDE: approved identifier")

    def test_extended_property_and_value_signals_are_evidence(self) -> None:
        described = classify_sensitivity("Value1", extended_property="Parent mobile number")
        detected = classify_sensitivity("Value2", values=("student@example.test",))
        self.assertEqual(described.category, "PII")
        self.assertEqual(described.confidence, "MEDIUM")
        self.assertEqual(detected.category, "PII")
        self.assertTrue(detected.evidence.startswith("VALUE_SIGNAL:"))


if __name__ == "__main__":
    unittest.main()
