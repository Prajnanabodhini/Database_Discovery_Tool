from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "test.yml"


def test_ci_gate_is_windows_offline_and_evidence_preserving() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    required = (
        "actions/checkout@v7",
        "actions/setup-python@v7",
        "runs-on: windows-latest",
        'python-version: "3.11"',
        'python -m pip install -e ".[test]"',
        "python -m compileall -q main.py src",
        "import mssql_database_documenter.web.app",
        'python -m pytest -q -p no:cacheprovider -m "not live" tests',
        "Test-Path -LiteralPath $runtimeRoot",
        "Test-Path -LiteralPath $_",
    )
    for expected in required:
        assert expected in source
    assert "secrets." not in source
    assert source.count("output") >= 2
    assert source.count("git_export") >= 2


def test_local_ci_equivalent_is_documented() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    operator_guide = (PROJECT_ROOT / "OPERATOR_RUN_GUIDE.md").read_text(encoding="utf-8")
    for source in (readme, operator_guide):
        assert "python main.py self-test" in source
