"""
Quick CLI tool to inspect the structure of an HDF5 file.

Usage:
    python -m tool.inspect_hdf5 path/to/file.h5

Responsibility:
- Open an HDF5 file in read-only mode.
- Print the tree of groups and datasets with shapes and dtypes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py


def _print_tree(name: str, obj, indent: int = 0) -> None:
    """Recursive helper to print groups and datasets."""
    prefix = "  " * indent
    if isinstance(obj, h5py.Dataset):
        print(f"{prefix}- {name} [Dataset] shape={obj.shape}, dtype={obj.dtype}")
    elif isinstance(obj, h5py.Group):
        # Print group header
        print(f"{prefix}- {name} [Group]")
        # Recurse into children
        for key, child in obj.items():
            _print_tree(f"{name}/{key}" if name != "/" else f"/{key}", child, indent + 1)


def inspect_hdf5(path: str) -> None:
    """Inspect and print the structure of an HDF5 file.

    Resolution strategy:
    - If `path` is absolute and exists -> use it.
    - If `path` is relative:
        * first try `<project_root>/data_repository/<path>`
        * then fall back to current working directory.
    """
    raw_path = Path(path)

    # Project root = parent of "src" directory (this file is under src/tool/)
    project_root = Path(__file__).resolve().parents[2]
    data_repo = project_root / "data_repository"

    file_path: Path
    if raw_path.is_absolute():
        file_path = raw_path
    else:
        candidate = data_repo / raw_path
        if candidate.exists():
            file_path = candidate
        else:
            file_path = raw_path

    if not file_path.exists():
        print(f"Error: file not found: {file_path}")
        return

    try:
        with h5py.File(file_path, "r") as f:
            print(f"HDF5 file: {file_path}")
            # Root-level attributes
            if f.attrs:
                print("Root attributes:")
                for key, value in f.attrs.items():
                    print(f"  - {key}: {value}")
            else:
                print("Root attributes: (none)")

            print("Structure:")
            _print_tree("/", f, indent=0)
    except OSError as exc:
        print(f"Error: cannot open HDF5 file: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect HDF5 file structure.")
    parser.add_argument("file", help="Path to the HDF5 file to inspect.")
    args = parser.parse_args()
    inspect_hdf5(args.file)


if __name__ == "__main__":
    main()


