"""Structural relationship inference helpers."""

from __future__ import annotations

import re


def normalized_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())
