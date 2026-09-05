"""Input normalization that preserves canonical evidence values."""

from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Any
import unicodedata


def raise_csv_field_limit() -> None:
    limit = sys.maxsize
    while limit > 131_072:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    raise_csv_field_limit()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stable_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def stable_key(value: Any) -> str:
    """Normalize identity text without altering canonical source evidence."""
    return unicodedata.normalize("NFKC", stable_text(value)).strip().casefold()


def number(value: Any) -> float | None:
    if value in (None, "", "None", "NULL"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None
