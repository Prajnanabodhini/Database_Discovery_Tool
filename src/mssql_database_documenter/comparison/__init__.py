"""Two/three-run comparison services plus v2 compatibility exports."""

from .engine import compare_run_paths
from .exporters import export_comparison
from .loaders import RunSnapshot, load_run
from .normalizers import read_csv_rows as _read_rows
from .diff import compare_rows


def write_database_comparison(output_root, runs):
    """Compatibility wrapper for the earlier two-database comparison API."""
    snapshots = [load_run(path, label=database) for database, path in runs.items()]
    result = compare_run_paths(snapshots)
    export_comparison(result, output_root, fixed_names=True)
    return result


__all__ = [
    "RunSnapshot", "compare_rows", "compare_run_paths", "export_comparison",
    "load_run", "write_database_comparison", "_read_rows",
]
