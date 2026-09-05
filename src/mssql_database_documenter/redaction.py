"""Conservative secret redaction for diagnostics and errors."""

from __future__ import annotations

import re


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|pwd|token|secret|api[_-]?key|access[_-]?key)\s*=\s*([^;\s]+)"
)
_CONNECTION_PASSWORD = re.compile(r"(?i)(\b(?:PWD|PASSWORD)\s*=\s*)[^;]*")


def redact_text(value: object, *, sensitive_values: tuple[str, ...] = ()) -> str:
    text = str(value)
    text = _CONNECTION_PASSWORD.sub(r"\1[REDACTED]", text)
    text = _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    for sensitive_value in sorted(
        (item for item in sensitive_values if item), key=len, reverse=True
    ):
        variants = (sensitive_value.replace("\\", "\\\\"), sensitive_value)
        for variant in variants:
            text = text.replace(variant, "[REDACTED]")
    return text
