"""Explicit offline developer self-test runner, isolated from discovery runtime."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .redaction import redact_text


SELF_TEST_ARGV = (
    sys.executable,
    "-m",
    "pytest",
    "-q",
    "-p",
    "no:cacheprovider",
    "-m",
    "not live",
    "tests",
)
_SENSITIVE_ENV_MARKERS = ("PASSWORD", "PWD", "SECRET", "TOKEN", "API_KEY", "ACCESS_KEY")


def _sensitive_environment_values() -> tuple[str, ...]:
    return tuple(
        value
        for name, value in os.environ.items()
        if value and any(marker in name.upper() for marker in _SENSITIVE_ENV_MARKERS)
    )


def _summary(stdout: object, stderr: object) -> str:
    lines = [line.strip() for line in f"{stdout or ''}\n{stderr or ''}".splitlines() if line.strip()]
    text = lines[-1] if lines else "No test summary was emitted."
    return redact_text(text[:1000], sensitive_values=_sensitive_environment_values())


def run_self_test(*, project_root: Path | None = None) -> dict[str, Any]:
    """Run the fixed offline pytest suite without loading discovery configuration."""
    root = (project_root or Path(__file__).resolve().parents[2]).resolve()
    runtime_roots = (root / "output", root / "git_export")
    existed_before = tuple(path.exists() for path in runtime_roots)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MSSQL_DOC_SELF_TEST"] = "1"

    try:
        completed = subprocess.run(
            SELF_TEST_ARGV,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            shell=False,
            env=environment,
        )
        returncode = completed.returncode
        summary = _summary(completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        summary = _summary(exc.stdout, "Offline self-test timed out after 180 seconds.")
    except OSError as exc:
        returncode = 2
        summary = redact_text(exc, sensitive_values=_sensitive_environment_values())[:1000]

    created_runtime_root = any(
        not existed and path.exists()
        for path, existed in zip(runtime_roots, existed_before, strict=True)
    )
    status = "PASS" if returncode == 0 and not created_runtime_root else "FAIL"
    return {
        "status": status,
        "scope": "offline-developer-tests",
        "pytest_invoked": True,
        "connection_attempted": False,
        "output_or_export_created": created_runtime_root,
        "returncode": returncode,
        "summary": summary,
    }
