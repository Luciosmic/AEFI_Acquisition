"""
HDF5 implementation of the scan export port.

Responsibility:
- Implement `IScanExportPort` to export scan point results into an HDF5 file.
- Store positions and measurements in resizable datasets for efficient access.

Rationale:
- Provide a structured, scalable format for scientific post-processing of scans.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import h5py
import numpy as np

from src.application.services.scan_application_service.ports.i_scan_export_port import (
    IScanExportPort,
)


logger = logging.getLogger(__name__)


@dataclass
class Hdf5ScanExportPort(IScanExportPort):
    """
    HDF5-based implementation of `IScanExportPort` for scan point results.

    Data layout (per file):
    - Attributes on root:
        * scan-level metadata (scan_id, pattern, grid, etc.)
    - Datasets under `/scan_data`:
        * positions: shape (N, 2)   -> columns: [x, y]
        * measurements: shape (N, 6)-> mean voltages
        * std_dev: shape (N, 6)     -> standard deviations
    """

    base_output_dir: Path = field(
        default_factory=lambda: Path("data_repository")
    )

    _file_path: Optional[Path] = field(init=False, default=None)
    _file: Optional[h5py.File] = field(init=False, default=None)
    _pos_dset = None
    _meas_dset = None
    _std_dset = None
    _index: int = field(init=False, default=0)

    def configure(
        self, directory: str, filename: str, metadata: Dict[str, Any]
    ) -> None:
        """
        Configure the export destination.

        - `directory`: if absolute, used as-is; if relative or empty,
          resolved under `base_output_dir`.
        - `filename`: logical base name; this implementation prepends
          a timestamp and appends `.h5`.
        - `metadata`: persisted as root attributes when file is opened.
        """
        if directory:
            dir_path = Path(directory)
            if not dir_path.is_absolute():
                dir_path = self.base_output_dir / dir_path
        else:
            dir_path = self.base_output_dir

        dir_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_base = "".join(c for c in filename if c.isalnum() or c in ("-", "_"))
        final_name = f"{timestamp}_{safe_base}.h5"

        self._file_path = dir_path / final_name
        self._metadata = metadata or {}
        logger.debug("HDF5 scan export configured at %s", self._file_path)

    def start(self) -> None:
        """Open the HDF5 file and create resizable datasets."""
        if self._file_path is None:
            raise RuntimeError("Hdf5ScanExportPort.configure() must be called before start().")

        if self._file is not None:
            # Already started.
            return

        self._file = h5py.File(self._file_path, "w")
        root = self._file

        # Store metadata as attributes for traceability.
        for key, value in self._metadata.items():
            try:
                root.attrs[key] = value
            except TypeError:
                # Fallback: string representation for non-serializable types.
                root.attrs[key] = str(value)

        scan_group = root.create_group("scan_data")

        # Positions: (x, y)
        self._pos_dset = scan_group.create_dataset(
            "positions",
            shape=(0, 2),
            maxshape=(None, 2),
            dtype="f8",
            chunks=True,
        )

        # Measurements: 6 components
        self._meas_dset = scan_group.create_dataset(
            "measurements",
            shape=(0, 6),
            maxshape=(None, 6),
            dtype="f8",
            chunks=True,
        )

        # Standard deviations: 6 components
        self._std_dset = scan_group.create_dataset(
            "std_dev",
            shape=(0, 6),
            maxshape=(None, 6),
            dtype="f8",
            chunks=True,
        )

        self._index = 0

    def write_point(self, data: Dict[str, Any]) -> None:
        """
        Append a single point to the datasets.

        Expected keys in `data` (as produced by `ScanExportService._flatten_point`):
        - x, y
        - voltage_* (6 fields)
        - std_dev_* (6 fields)
        """
        if self._file is None or self._pos_dset is None:
            raise RuntimeError("Hdf5ScanExportPort.start() must be called before write_point().")

        x = float(data["x"])
        y = float(data["y"])

        meas = np.array(
            [
                float(data["voltage_x_in_phase"]),
                float(data["voltage_x_quadrature"]),
                float(data["voltage_y_in_phase"]),
                float(data["voltage_y_quadrature"]),
                float(data["voltage_z_in_phase"]),
                float(data["voltage_z_quadrature"]),
            ],
            dtype="f8",
        )

        # Std devs may be None if not computed; replace None by NaN for clarity.
        std_vals = [
            data.get("std_dev_x_in_phase"),
            data.get("std_dev_x_quadrature"),
            data.get("std_dev_y_in_phase"),
            data.get("std_dev_y_quadrature"),
            data.get("std_dev_z_in_phase"),
            data.get("std_dev_z_quadrature"),
        ]
        std = np.array(
            [np.nan if v is None else float(v) for v in std_vals],
            dtype="f8",
        )

        new_size = self._index + 1
        self._pos_dset.resize((new_size, 2))
        self._meas_dset.resize((new_size, 6))
        self._std_dset.resize((new_size, 6))

        self._pos_dset[self._index, :] = [x, y]
        self._meas_dset[self._index, :] = meas
        self._std_dset[self._index, :] = std

        self._index = new_size

    def stop(self) -> None:
        """Close the HDF5 file."""
        if self._file is not None:
            try:
                self._file.flush()
            finally:
                self._file.close()

        self._file = None
        self._pos_dset = None
        self._meas_dset = None
        self._std_dset = None
        self._file_path = None
        self._index = 0



