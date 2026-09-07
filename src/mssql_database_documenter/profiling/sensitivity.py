"""Conservative, overrideable sensitivity classification and masking."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import hashlib
from pathlib import Path
import re
import tomllib
from typing import Iterable


SENSITIVE_CATEGORIES = frozenset(
    {"Credential", "PII", "Financial", "Health", "Potentially Sensitive"}
)
VALID_CATEGORIES = SENSITIVE_CATEGORIES | {"Unknown", "Non-sensitive"}
VALID_ACTIONS = frozenset({"REDACT", "PSEUDONYMIZE", "PRESERVE"})


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    category: str
    action: str
    confidence: str
    evidence: str


@dataclass(frozen=True, slots=True)
class SensitivityRule:
    database: str = "*"
    schema: str = "*"
    table: str = "*"
    column: str = "*"
    match: str = "pattern"
    category: str = "PII"
    action: str = "PSEUDONYMIZE"
    confidence: str = "HIGH"
    reason: str = "operator override"

    def matches(self, database: str, schema: str, table: str, column: str) -> bool:
        actual = (database.casefold(), schema.casefold(), table.casefold(), column.casefold())
        expected = (self.database.casefold(), self.schema.casefold(), self.table.casefold(), self.column.casefold())
        if self.match == "exact":
            return all(wanted in {"", "*"} or wanted == value for wanted, value in zip(expected, actual, strict=True))
        return all(fnmatchcase(value, wanted or "*") for wanted, value in zip(expected, actual, strict=True))


def load_sensitivity_overrides(path: Path | None) -> tuple[SensitivityRule, ...]:
    """Load exact/pattern rules. Exact rules take precedence; file order breaks ties."""
    if path is None or not path.is_file():
        return ()
    with path.open("rb") as handle:
        payload = tomllib.load(handle)
    rules: list[tuple[int, SensitivityRule]] = []
    for index, raw in enumerate(payload.get("rules", []), 1):
        if not isinstance(raw, dict):
            raise ValueError(f"Sensitivity override rule {index} must be a TOML table")
        match = str(raw.get("match", "pattern")).strip().casefold()
        category = str(raw.get("category", "PII")).strip()
        action = str(raw.get("action", "PSEUDONYMIZE")).strip().upper()
        confidence = str(raw.get("confidence", "HIGH")).strip().upper()
        if match not in {"exact", "pattern"}:
            raise ValueError(f"Sensitivity override rule {index} has invalid match type")
        if category not in VALID_CATEGORIES or action not in VALID_ACTIONS:
            raise ValueError(f"Sensitivity override rule {index} has invalid category/action")
        rules.append((index, SensitivityRule(
            database=str(raw.get("database", "*")), schema=str(raw.get("schema", "*")),
            table=str(raw.get("table", "*")), column=str(raw.get("column", "*")),
            match=match, category=category, action=action, confidence=confidence,
            reason=str(raw.get("reason", "operator override")),
        )))
    rules.sort(key=lambda item: (item[1].match != "exact", item[0]))
    return tuple(rule for _, rule in rules)


_CREDENTIAL = re.compile(r"password|passwd|pwd|secret|token|api.?key|credential|salt|hash", re.I)
_FINANCIAL = re.compile(r"bank|account.?no|iban|swift|card|cvv|salary|income|payment", re.I)
_HEALTH = re.compile(r"health|medical|diagnos|disease|blood|patient", re.I)
_PII = re.compile(r"email|e.?mail|phone|mobile|address|aadhaar|aadhar|pan.?no|passport|dob|birth|father|mother|guardian|name", re.I)
_POTENTIAL = re.compile(r"user|login|ip.?address|location|photo|signature|remark|note", re.I)

_LEGACY_PII = frozenset({
    "studnm", "studname", "sname", "fname", "mname", "fathernm", "mothernm",
    "guardiannm", "mobno", "mobileno", "phno", "phoneno", "contactno", "addr1",
    "addr2", "resadd", "paddr", "dob", "bdate", "birthdt", "aadhaar", "aadhar",
    "panno", "passport", "email", "emailid", "emailaddr",
})

_VALUE_SIGNALS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("PII", re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$"), "email value pattern"),
    ("PII", re.compile(r"^(?:\+?\d[\d ()-]{7,}\d)$"), "phone value pattern"),
    ("PII", re.compile(r"^\d{4}[ -]?\d{4}[ -]?\d{4}$"), "Aadhaar-like value pattern"),
    ("PII", re.compile(r"^[A-Z]{5}\d{4}[A-Z]$", re.I), "PAN-like value pattern"),
)


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def classify_sensitivity(
    column_name: str,
    *,
    database: str = "",
    schema: str = "",
    table: str = "",
    extended_property: str = "",
    values: Iterable[object] = (),
    overrides: Iterable[SensitivityRule] = (),
) -> SensitivityResult:
    for rule in overrides:
        if rule.matches(database, schema, table, column_name):
            return SensitivityResult(rule.category, rule.action, rule.confidence, f"OVERRIDE: {rule.reason}")

    normalized = _normalized(column_name)
    if normalized in _LEGACY_PII:
        return SensitivityResult("PII", "PSEUDONYMIZE", "HIGH", "BUILTIN_LEGACY_COLUMN_NAME")
    for category, pattern in (("Credential", _CREDENTIAL), ("Financial", _FINANCIAL), ("Health", _HEALTH), ("PII", _PII), ("Potentially Sensitive", _POTENTIAL)):
        if pattern.search(column_name):
            return SensitivityResult(category, "REDACT" if category == "Credential" else "PSEUDONYMIZE", "HIGH", "BUILTIN_COLUMN_NAME")
    if extended_property:
        for category, pattern in (("Credential", _CREDENTIAL), ("Financial", _FINANCIAL), ("Health", _HEALTH), ("PII", _PII), ("Potentially Sensitive", _POTENTIAL)):
            if pattern.search(extended_property):
                return SensitivityResult(category, "REDACT" if category == "Credential" else "PSEUDONYMIZE", "MEDIUM", "EXTENDED_PROPERTY_HEURISTIC")
    for value in values:
        text = str(value or "").strip()
        if not text or text.startswith("[MASKED:") or text == "[REDACTED]":
            continue
        for category, pattern, evidence in _VALUE_SIGNALS:
            if pattern.fullmatch(text):
                return SensitivityResult(category, "PSEUDONYMIZE", "HIGH", f"VALUE_SIGNAL: {evidence}")
    return SensitivityResult("Unknown", "PRESERVE", "LOW", "NO_SENSITIVITY_SIGNAL")


def mask_value(value: object, category: str, salt: str, masking_enabled: bool = True) -> object:
    if value is None:
        return None
    if category == "Credential":
        return "[REDACTED]"
    if masking_enabled and category in SENSITIVE_CATEGORIES:
        digest = hashlib.sha256(f"{salt}|{value}".encode("utf-8", errors="replace")).hexdigest()[:16]
        return f"[MASKED:{digest}]"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "[BINARY_REDACTED]"
    return value


__all__ = (
    "SENSITIVE_CATEGORIES", "SensitivityResult", "SensitivityRule", "classify_sensitivity",
    "load_sensitivity_overrides", "mask_value",
)
