"""Fail-closed validation for every project-owned SQL statement."""

from __future__ import annotations

import re


class UnsafeSqlError(ValueError):
    """Raised when a SQL statement is not demonstrably read-only."""


_FORBIDDEN_TOKENS = frozenset(
    {
        "ALTER", "BACKUP", "BEGIN", "BULK", "CHECKPOINT", "COMMIT", "CREATE",
        "DBCC", "DELETE", "DENY", "DISABLE", "DROP", "ENABLE", "EXEC",
        "EXECUTE", "GRANT", "INSERT", "INTO", "KILL", "MERGE", "RECONFIGURE",
        "RESTORE", "REVOKE", "ROLLBACK", "SAVE", "SHUTDOWN", "TRUNCATE",
        "UPDATE", "USE", "WAITFOR",
    }
)
_FORBIDDEN_PHRASES = (
    re.compile(r"\bNEXT\s+VALUE\s+FOR\b", re.IGNORECASE),
    re.compile(r"\bOPENQUERY\s*\(", re.IGNORECASE),
    re.compile(r"\bOPENROWSET\s*\(", re.IGNORECASE),
    re.compile(r"\bOPENDATASOURCE\s*\(", re.IGNORECASE),
)


def _strip_comments_and_literals(sql: str) -> str:
    """Replace comments and quoted content while preserving token boundaries."""
    output: list[str] = []
    index = 0
    state = "normal"
    while index < len(sql):
        char = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""
        if state == "normal":
            if char == "-" and following == "-":
                state = "line_comment"
                output.extend("  ")
                index += 2
                continue
            if char == "/" and following == "*":
                state = "block_comment"
                output.extend("  ")
                index += 2
                continue
            if char == "'":
                state = "string"
                output.append(" ")
                index += 1
                continue
            if char == '"':
                state = "quoted_identifier"
                output.append(" ")
                index += 1
                continue
            if char == "[":
                state = "bracket_identifier"
                output.append(" ")
                index += 1
                continue
            output.append(char)
            index += 1
            continue
        if state == "line_comment":
            if char in "\r\n":
                state = "normal"
                output.append(char)
            else:
                output.append(" ")
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and following == "/":
                state = "normal"
                output.extend("  ")
                index += 2
            else:
                output.append(" ")
                index += 1
            continue
        if state in {"string", "quoted_identifier"}:
            delimiter = "'" if state == "string" else '"'
            if char == delimiter and following == delimiter:
                output.extend("  ")
                index += 2
            elif char == delimiter:
                state = "normal"
                output.append(" ")
                index += 1
            else:
                output.append(" ")
                index += 1
            continue
        if state == "bracket_identifier":
            if char == "]" and following == "]":
                output.extend("  ")
                index += 2
            elif char == "]":
                state = "normal"
                output.append(" ")
                index += 1
            else:
                output.append(" ")
                index += 1
    if state in {"string", "quoted_identifier", "bracket_identifier", "block_comment"}:
        raise UnsafeSqlError(f"Unterminated SQL {state.replace('_', ' ')}")
    return "".join(output)


def validate_read_only_sql(sql: str) -> str:
    """Return SQL unchanged if it is one safe SELECT statement; otherwise deny it."""
    if not isinstance(sql, str) or not sql.strip():
        raise UnsafeSqlError("SQL must be a non-empty string")
    scrubbed = _strip_comments_and_literals(sql).strip()
    if not scrubbed:
        raise UnsafeSqlError("SQL contains no executable statement")

    without_trailing = scrubbed[:-1].rstrip() if scrubbed.endswith(";") else scrubbed
    if ";" in without_trailing:
        raise UnsafeSqlError("Multiple SQL statements are not allowed")

    first_match = re.match(r"[A-Za-z]+", without_trailing)
    first_token = first_match.group(0).upper() if first_match else ""
    if first_token not in {"SELECT", "WITH"}:
        raise UnsafeSqlError("Only SELECT or WITH ... SELECT statements are allowed")
    if first_token == "WITH" and not re.search(r"\bSELECT\b", without_trailing, re.IGNORECASE):
        raise UnsafeSqlError("A CTE must resolve to a SELECT statement")

    tokens = {token.upper() for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", without_trailing)}
    forbidden = sorted(tokens & _FORBIDDEN_TOKENS)
    if forbidden:
        raise UnsafeSqlError(f"Forbidden SQL token(s): {', '.join(forbidden)}")
    for pattern in _FORBIDDEN_PHRASES:
        if pattern.search(without_trailing):
            raise UnsafeSqlError(f"Forbidden SQL construct: {pattern.pattern}")
    return sql


class ReadOnlyCursor:
    """Minimal cursor proxy that validates SQL at the final execution boundary."""

    def __init__(self, cursor: object) -> None:
        self._cursor = cursor

    def execute(self, sql: str, *parameters: object) -> object:
        validate_read_only_sql(sql)
        return self._cursor.execute(sql, *parameters)  # type: ignore[attr-defined]

    def executemany(self, *_args: object, **_kwargs: object) -> object:
        raise UnsafeSqlError("executemany is not available in read-only mode")

    @property
    def description(self) -> object:
        return self._cursor.description  # type: ignore[attr-defined]

    @property
    def rowcount(self) -> object:
        return self._cursor.rowcount  # type: ignore[attr-defined]

    def fetchone(self) -> object:
        return self._cursor.fetchone()  # type: ignore[attr-defined]

    def fetchmany(self, size: int | None = None) -> object:
        if size is None:
            return self._cursor.fetchmany()  # type: ignore[attr-defined]
        return self._cursor.fetchmany(size)  # type: ignore[attr-defined]

    def fetchall(self) -> object:
        return self._cursor.fetchall()  # type: ignore[attr-defined]

    def __getattr__(self, name: str) -> object:
        raise UnsafeSqlError(f"Cursor capability {name!r} is not exposed in read-only mode")
