"""Fail-closed destination containment for generated artifacts."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
from typing import Iterable


class UnsafeDestinationError(ValueError):
    """Raised before a generated-artifact path can escape its configured root."""


def path_exists_no_follow(path: Path) -> bool:
    """Return true for ordinary paths, broken links, and Windows reparse points."""
    return os.path.lexists(path)


def is_reparse_point(path: Path) -> bool:
    """Detect symbolic links and Windows junction/reparse points without following."""
    try:
        details = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafeDestinationError(f"Cannot inspect destination path component: {path.name}") from exc
    junction_check = getattr(path, "is_junction", None)
    try:
        is_junction = bool(junction_check()) if junction_check else False
    except OSError as exc:
        raise UnsafeDestinationError(f"Cannot inspect destination junction: {path.name}") from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = int(getattr(details, "st_file_attributes", 0))
    return path.is_symlink() or is_junction or bool(attributes & reparse_flag)


def _component(value: object) -> str:
    text = str(value)
    if (
        not text
        or text in {".", ".."}
        or Path(text).is_absolute()
        or PureWindowsPath(text).is_absolute()
        or PurePosixPath(text).is_absolute()
        or len(PureWindowsPath(text).parts) != 1
        or len(PurePosixPath(text).parts) != 1
    ):
        raise UnsafeDestinationError("Destination path component is invalid")
    return text


def _canonical_root(root: Path | str) -> Path:
    configured = Path(root)
    if not path_exists_no_follow(configured):
        configured.mkdir(parents=True, exist_ok=False)
    if not configured.is_dir():
        raise UnsafeDestinationError("Configured destination root is not a directory")
    try:
        return configured.resolve(strict=True)
    except OSError as exc:
        raise UnsafeDestinationError("Configured destination root cannot be resolved") from exc


def ensure_contained_directory(
    root: Path | str,
    components: Iterable[object] = (),
    *,
    create: bool = True,
) -> Path:
    """Validate each child before descending, optionally creating one level at a time."""
    canonical_root = _canonical_root(root)
    current = canonical_root
    for raw_component in components:
        component = _component(raw_component)
        candidate = current / component
        if path_exists_no_follow(candidate):
            if is_reparse_point(candidate):
                raise UnsafeDestinationError(f"Destination path contains a link or reparse point: {component}")
            if not candidate.is_dir():
                raise UnsafeDestinationError(f"Destination path component is not a directory: {component}")
        elif create:
            candidate.mkdir(exist_ok=False)
        else:
            raise UnsafeDestinationError(f"Destination directory does not exist: {component}")
        if is_reparse_point(candidate):
            raise UnsafeDestinationError(f"Destination path became a link or reparse point: {component}")
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(canonical_root)
        except (OSError, ValueError) as exc:
            raise UnsafeDestinationError(f"Destination path escapes its configured root: {component}") from exc
        current = resolved
    return current


def new_contained_path(root: Path | str, components: Iterable[object]) -> Path:
    """Return a nonexistent child whose validated parent is contained by root."""
    parts = tuple(components)
    if not parts:
        raise UnsafeDestinationError("A destination child path is required")
    parent = ensure_contained_directory(root, parts[:-1])
    leaf = _component(parts[-1])
    candidate = parent / leaf
    if path_exists_no_follow(candidate):
        raise UnsafeDestinationError(f"Destination already exists or is a link: {leaf}")
    try:
        parent.resolve(strict=True).relative_to(_canonical_root(root))
    except (OSError, ValueError) as exc:
        raise UnsafeDestinationError("Destination parent escapes its configured root") from exc
    return candidate
