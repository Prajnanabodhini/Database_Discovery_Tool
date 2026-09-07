import ast
import inspect
from pathlib import Path
import unittest

from mssql_database_documenter.fullrun import SequentialRun


class FullRunModularizationTests(unittest.TestCase):
    def test_domain_methods_have_explicit_module_owners(self) -> None:
        expected = {
            "prompt07_profile": ".profiling.stages",
            "prompt10_relationships": ".relationships.stages",
            "prompt11_lineage": ".lineage.stages",
            "prompt13_classification": ".analysis.stages",
            "prompt15_outputs": ".reporting.stages",
            "_snapshot_integrity": ".reporting.stages",
        }
        for method_name, module_suffix in expected.items():
            with self.subTest(method=method_name):
                owner = inspect.getmodule(getattr(SequentialRun, method_name))
                self.assertIsNotNone(owner)
                self.assertTrue(owner.__name__.endswith(module_suffix), owner.__name__)

    def test_orchestrator_retains_lifecycle_and_stage_gates(self) -> None:
        expected = {
            "__init__", "stage", "skip_stage", "_error", "fetch", "fetch_dynamic",
            "prompt02_safety", "prompt03_connection", "prompt04_metadata",
            "prompt16_safety_review", "run", "resume_after_comparison",
        }
        for method_name in expected:
            with self.subTest(method=method_name):
                owner = inspect.getmodule(getattr(SequentialRun, method_name))
                self.assertEqual(owner.__name__, "mssql_database_documenter.fullrun")

    def test_domain_modules_do_not_import_fullrun(self) -> None:
        package = Path(inspect.getfile(SequentialRun)).parent
        paths = [
            package / "profiling" / "stages.py",
            package / "relationships" / "stages.py",
            package / "lineage" / "stages.py",
            package / "analysis" / "stages.py",
            package / "reporting" / "stages.py",
        ]
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            imported.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            with self.subTest(module=path.parent.name):
                self.assertFalse(any(name.endswith("fullrun") for name in imported))

    def test_fullrun_has_meaningfully_reduced_domain_logic(self) -> None:
        fullrun_path = Path(inspect.getfile(SequentialRun))
        self.assertLess(len(fullrun_path.read_text(encoding="utf-8").splitlines()), 500)


if __name__ == "__main__":
    unittest.main()
