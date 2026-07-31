"""
HDF5 implementation of the scan export port.

Responsibility:
- Implement `IScanExportPort` to export scan point results into an HDF5 file.
- Store positions and measurements in resizable datasets for efficient access.

Rationale:
- Provide a structured, scalable format for scientific post-processing of scans.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import h5py
import numpy as np

from application.services.scan_export_service.ports.i_scan_export_port import (
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
        * baseline_measurements: shape (N, 6) -> excitation-muted baseline
          voltages (differential mode only; NaN-filled rows for a
          non-differential scan — no baseline_std_dev counterpart since
          ScanExportService never computes/forwards one)
    - Datasets under `/electric_field_data` (if field probe is used):
        * field_positions: shape (M, 2) -> columns: [x, y]
        * field_measurements: shape (M, P) -> P components (varies by probe)
        * field_std_dev: shape (M, P) -> standard deviations for each component
        * baseline_field_measurements: shape (M, P) -> excitation-muted
          baseline field components (differential mode only; NaN-filled
          otherwise)
        * baseline_field_std_dev: shape (M, P) -> standard deviations for
          the baseline field components (NaN-filled otherwise)
        * probe_info: attributes with probe metadata (brand, model, serial, axes)
    """

    base_output_dir: Path = field(
        default_factory=lambda: Path.home() / "Desktop" / "AEFI_Acquisition_Exports"
    )

    _file_path: Optional[Path] = field(init=False, default=None)
    _file: Optional[h5py.File] = field(init=False, default=None)
    _pos_dset = None
    _meas_dset = None
    _std_dset = None
    _baseline_meas_dset = None
    _field_pos_dset = None
    _field_meas_dset = None
    _field_std_dset = None
    _field_baseline_meas_dset = None
    _field_baseline_std_dset = None
    _field_index: int = field(init=False, default=0)
    _field_n_components: int = field(init=False, default=0)
    _index: int = field(init=False, default=0)

    def configure(
        self, directory: str, filename: str, metadata: Dict[str, Any], timestamp: Optional[str] = None
    ) -> None:
        """
        Configure the export destination.

        - `directory`: if absolute, used as-is; if relative or empty,
          resolved under `base_output_dir`.
        - `filename`: scan name (without date/time or extension).
        - `metadata`: persisted as root attributes when file is opened.
        - `timestamp`: reuse a caller-supplied stamp instead of generating
          one, so this port lands in the same acquisition folder as a
          sibling port configured for the same scan.

        One acquisition is one bounded context: the file lands in its own
        acquisition folder `<dir>/YYYY-MM-DD_HHMMSS_stepScan_<name>/`, named
        `YYYY-MM-DD_HHMMSS_stepScan_<name>.h5` (same convention as the CSV
        port's acquisition folder, minus the per-device split since HDF5
        bundles device + probe data into one file).
        """
        if directory:
            dir_path = Path(directory)
            if not dir_path.is_absolute():
                dir_path = self.base_output_dir / dir_path
        else:
            dir_path = self.base_output_dir

        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_base = "".join(c for c in filename if c.isalnum() or c in ("-", "_"))

        acquisition_dir = dir_path / f"{timestamp}_stepScan_{safe_base}"
        acquisition_dir.mkdir(parents=True, exist_ok=True)
        final_name = f"{timestamp}_stepScan_{safe_base}.h5"

        self._file_path = acquisition_dir / final_name
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

        # Differential-mode baseline (excitation muted): 6 components.
        # Always created, NaN-filled per point when the scan isn't
        # differential — mirrors measurements/std_dev rather than being
        # conditionally present, so downstream readers can rely on the key.
        self._baseline_meas_dset = scan_group.create_dataset(
            "baseline_measurements",
            shape=(0, 6),
            maxshape=(None, 6),
            dtype="f8",
            chunks=True,
        )

        self._index = 0
        self._field_index = 0
        self._field_n_components = 0

    def configure_field_data(self, n_components: int, probe_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Configure the electric field datasets.
        
        Must be called before write_field_point() if exporting field measurements.
        
        Args:
            n_components: Number of components in the field measurements (e.g., 3 for tri-axial)
            probe_info: Optional dictionary with probe metadata (brand, model, serial, axis_labels)
        """
        if self._file is None:
            raise RuntimeError("Hdf5ScanExportPort.start() must be called before configure_field_data().")
        
        self._field_n_components = n_components
        root = self._file
        
        # Create electric field group
        ef_group = root.create_group("electric_field_data")
        
        # Store probe info as attributes
        if probe_info:
            for key, value in probe_info.items():
                try:
                    ef_group.attrs[key] = value
                except TypeError:
                    ef_group.attrs[key] = str(value)
        
        # Create resizable datasets for electric field data
        self._field_pos_dset = ef_group.create_dataset(
            "field_positions",
            shape=(0, 2),
            maxshape=(None, 2),
            dtype="f8",
            chunks=True,
        )
        
        self._field_meas_dset = ef_group.create_dataset(
            "field_measurements",
            shape=(0, n_components),
            maxshape=(None, n_components),
            dtype="f8",
            chunks=True,
        )
        
        self._field_std_dset = ef_group.create_dataset(
            "field_std_dev",
            shape=(0, n_components),
            maxshape=(None, n_components),
            dtype="f8",
            chunks=True,
        )

        # Differential-mode baseline (excitation muted), always created —
        # NaN-filled per point when the scan isn't differential.
        self._field_baseline_meas_dset = ef_group.create_dataset(
            "baseline_field_measurements",
            shape=(0, n_components),
            maxshape=(None, n_components),
            dtype="f8",
            chunks=True,
        )

        self._field_baseline_std_dset = ef_group.create_dataset(
            "baseline_field_std_dev",
            shape=(0, n_components),
            maxshape=(None, n_components),
            dtype="f8",
            chunks=True,
        )

        self._field_index = 0
        logger.debug("Electric field datasets configured for %d components", n_components)

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

        # Baseline (excitation muted) may be entirely absent for a
        # non-differential scan — NaN-fill rather than skipping the row.
        baseline_vals = [
            data.get("baseline_voltage_x_in_phase"),
            data.get("baseline_voltage_x_quadrature"),
            data.get("baseline_voltage_y_in_phase"),
            data.get("baseline_voltage_y_quadrature"),
            data.get("baseline_voltage_z_in_phase"),
            data.get("baseline_voltage_z_quadrature"),
        ]
        baseline = np.array(
            [np.nan if v is None else float(v) for v in baseline_vals],
            dtype="f8",
        )

        new_size = self._index + 1
        self._pos_dset.resize((new_size, 2))
        self._meas_dset.resize((new_size, 6))
        self._std_dset.resize((new_size, 6))
        self._baseline_meas_dset.resize((new_size, 6))

        self._pos_dset[self._index, :] = [x, y]
        self._meas_dset[self._index, :] = meas
        self._std_dset[self._index, :] = std
        self._baseline_meas_dset[self._index, :] = baseline

        self._index = new_size

    def write_field_point(self, data: Dict[str, Any]) -> None:
        """
        Append a single electric field measurement point to the datasets.
        
        Expected keys in `data`:
        - x, y (position)
        - field_components: tuple of component values
        - field_std_dev_components: tuple of standard deviations (or None)
        """
        if self._file is None or self._field_pos_dset is None:
            raise RuntimeError("Hdf5ScanExportPort.start() and configure_field_data() must be called before write_field_point().")
        
        x = float(data["x"])
        y = float(data["y"])
        components = tuple(float(c) for c in data["field_components"])
        std_dev_components = data.get("field_std_dev_components")
        
        # Convert std_dev_components to numpy array
        if std_dev_components is not None:
            std_devs = [np.nan if v is None else float(v) for v in std_dev_components]
        else:
            std_devs = [np.nan] * len(components)

        # Baseline (excitation muted) may be entirely absent for a
        # non-differential scan — NaN-fill rather than skipping the row.
        baseline_components = data.get("baseline_field_components")
        if baseline_components is not None:
            baseline_meas = [float(c) for c in baseline_components]
        else:
            baseline_meas = [np.nan] * self._field_n_components

        baseline_std_dev_components = data.get("baseline_field_std_dev_components")
        if baseline_std_dev_components is not None:
            baseline_std_devs = [np.nan if v is None else float(v) for v in baseline_std_dev_components]
        else:
            baseline_std_devs = [np.nan] * self._field_n_components

        new_size = self._field_index + 1
        self._field_pos_dset.resize((new_size, 2))
        self._field_meas_dset.resize((new_size, self._field_n_components))
        self._field_std_dset.resize((new_size, self._field_n_components))
        self._field_baseline_meas_dset.resize((new_size, self._field_n_components))
        self._field_baseline_std_dset.resize((new_size, self._field_n_components))

        self._field_pos_dset[self._field_index, :] = [x, y]
        self._field_meas_dset[self._field_index, :] = components
        self._field_std_dset[self._field_index, :] = std_devs
        self._field_baseline_meas_dset[self._field_index, :] = baseline_meas
        self._field_baseline_std_dset[self._field_index, :] = baseline_std_devs

        self._field_index = new_size

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """Write the acquisition's parameter snapshot as a JSON file next to
        the `.h5` file, in the same acquisition folder (kept as a real file
        rather than only root attrs, so a JSON manifest always exists
        regardless of the chosen export format)."""
        if self._file_path is None:
            raise RuntimeError("Hdf5ScanExportPort.configure() must be called before write_metadata().")

        metadata_path = self._file_path.parent / f"{self._file_path.stem}_acquisition-parameters.json"
        with metadata_path.open(mode="w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

    def get_output_path(self) -> Optional[Path]:
        """Path to the `.h5` file, once configured."""
        return self._file_path

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
        self._baseline_meas_dset = None
        self._field_pos_dset = None
        self._field_meas_dset = None
        self._field_std_dset = None
        self._field_baseline_meas_dset = None
        self._field_baseline_std_dset = None
        self._file_path = None
        self._index = 0
        self._field_index = 0
        self._field_n_components = 0


