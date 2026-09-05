"""Dual-root file browser and manifested run registry with containment checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from ..comparison.loaders import RunSnapshot, load_run


class PathSecurityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RootSpec:
    key: str
    label: str
    path: Path
    sanitized: bool = False


class FileBrowser:
    def __init__(self, output_root: Path, git_export_root: Path) -> None:
        self.roots = {
            "output": RootSpec("output", "Output", output_root.resolve(), False),
            "git_export": RootSpec("git_export", "Git Export", git_export_root.resolve(), True),
        }

    def root(self, key: str) -> RootSpec:
        try:
            return self.roots[key]
        except KeyError as exc:
            raise PathSecurityError("Unknown file root") from exc

    def resolve(self, key: str, relative: str = "", *, must_exist: bool = True) -> Path:
        spec = self.root(key)
        pure = PurePosixPath(relative.replace("\\", "/"))
        if Path(relative).is_absolute() or PureWindowsPath(relative).is_absolute() or pure.is_absolute() or ".." in pure.parts:
            raise PathSecurityError("Path traversal or absolute paths are not allowed")
        candidate = (spec.path / Path(*pure.parts)).resolve(strict=False)
        try:
            candidate.relative_to(spec.path)
        except ValueError as exc:
            raise PathSecurityError("Resolved path escapes the configured root") from exc
        if must_exist and not candidate.exists():
            raise FileNotFoundError(relative)
        if candidate.exists():
            resolved = candidate.resolve()
            try:
                resolved.relative_to(spec.path)
            except ValueError as exc:
                raise PathSecurityError("Symlink target escapes the configured root") from exc
        return candidate

    def list_directory(self, key: str, relative: str = "", *, search: str = "", extension: str = "") -> dict[str, Any]:
        spec = self.root(key)
        if not spec.path.exists():
            return {"root": key, "label": spec.label, "sanitized": spec.sanitized, "exists": False, "relative": "", "entries": [], "message": "No Git exports generated yet." if key == "git_export" else "No output runs generated yet."}
        directory = self.resolve(key, relative)
        if not directory.is_dir():
            raise NotADirectoryError(relative)
        entries = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
            try:
                path.resolve(strict=True).relative_to(spec.path)
            except (OSError, ValueError):
                # Never stat, classify, or expose a broken/out-of-root symlink.
                continue
            if search and search.casefold() not in path.name.casefold(): continue
            if extension and path.is_file() and path.suffix.casefold() != extension.casefold(): continue
            stat = path.stat()
            is_dir = path.is_dir()
            entries.append({"name": path.name, "relative": path.relative_to(spec.path).as_posix(), "is_dir": is_dir, "size": stat.st_size, "modified": stat.st_mtime, "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(), "extension": path.suffix.casefold(), "type": "Directory" if is_dir else (path.suffix.casefold().removeprefix(".").upper() or "File")})
        entries.sort(key=lambda item: (not item["is_dir"], item["name"].casefold()))
        breadcrumbs = []
        cumulative: list[str] = []
        for part in PurePosixPath(relative).parts:
            cumulative.append(part); breadcrumbs.append({"name": part, "relative": "/".join(cumulative)})
        parts = PurePosixPath(relative).parts
        database = parts[0] if key == "output" and len(parts) >= 1 else parts[1] if key == "git_export" and len(parts) >= 2 and parts[0].casefold() == "mssql" else ""
        run_id = parts[1] if key == "output" and len(parts) >= 2 else parts[2] if key == "git_export" and len(parts) >= 3 and parts[0].casefold() == "mssql" else ""
        return {"root": key, "label": spec.label, "sanitized": spec.sanitized, "exists": True, "relative": PurePosixPath(relative).as_posix() if relative else "", "breadcrumbs": breadcrumbs, "entries": entries, "database": database, "run": run_id}

    def scan_runs(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        patterns = {"output": "*/run_*", "git_export": "MSSQL/*/run_*"}
        for key, pattern in patterns.items():
            spec = self.root(key)
            if not spec.path.exists(): continue
            for path in sorted(spec.path.glob(pattern), reverse=True):
                try:
                    snapshot = load_run(path, label=path.name, origin=key)
                except (ValueError, OSError):
                    continue
                relative = path.resolve().relative_to(spec.path).as_posix()
                records.append({"ref": f"{key}:{relative}", "root": key, "relative": relative, "path": relative, "sanitized": spec.sanitized, **snapshot.summary})
        return records

    def load_ref(self, reference: str) -> RunSnapshot:
        key, separator, relative = reference.partition(":")
        if not separator: raise PathSecurityError("Invalid run reference")
        return load_run(self.resolve(key, relative), label=reference, origin=key)
