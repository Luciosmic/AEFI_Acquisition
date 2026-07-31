"""
CSV implementation of the scan export port.

Responsibility:
- Implement `IExportPort` to export scan point results to a CSV file.
- Write one row per scan point (position + aggregated measurement + std dev).

Rationale:
- Provide a quick, human-inspectable export format for verification.
"""

from __future__ import annotations

import os
import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, TextIO

from application.services.scan_export_service.ports.i_scan_export_port import (
    IScanExportPort,
)


logger = logging.getLogger(__name__)


@dataclass
class CsvScanExportPort(IScanExportPort):
    """
    CSV-based implementation of `IExportPort`.

    Notes:
    - By default, files are written under `~/Desktop/AEFI_Acquisition_Exports`
      (configurable via `directory` in `configure`).
    - The caller is responsible for providing a flat `data` dict with
      scalar values in `write_point`.
    """

    # Base directory used when `directory` passed to `configure` is relative or empty.
    base_output_dir: Path = field(
        default_factory=lambda: Path.home() / "Desktop" / "AEFI_Acquisition_Exports"
    )

    _file: Optional[TextIO] = field(init=False, default=None)
    _writer: Optional[csv.DictWriter] = field(init=False, default=None)
    _fieldnames: Optional[List[str]] = field(init=False, default=None)
    _configured_path: Optional[Path] = field(init=False, default=None)
    _dir_path: Optional[Path] = field(init=False, default=None)
    _timestamp: Optional[str] = field(init=False, default=None)

    # Electric field data goes to its own file (named after the probe, e.g.
    # "<timestamp>_narda_ep600.csv") rather than sharing the main file: its
    # points arrive via a separate call (write_field_point), not necessarily
    # in lockstep with write_point, so it can't share write_point's row/columns.
    _field_file: Optional[TextIO] = field(init=False, default=None)
    _field_writer: Optional[csv.DictWriter] = field(init=False, default=None)
    _field_fieldnames: Optional[List[str]] = field(init=False, default=None)
    _field_axis_labels: Optional[List[str]] = field(init=False, default=None)
    _scan_name: Optional[str] = field(init=False, default=None)

    def configure(
        self, directory: str, filename: str, metadata: Dict[str, Any], timestamp: Optional[str] = None
    ) -> None:
        """
        Configure the export destination and filename.

        - `directory`: if absolute, used as-is; if relative or empty, it is
          resolved under `base_output_dir`.
        - `filename`: scan name (without date/time, device tag, or extension).
        - `metadata`: currently unused here but kept for API symmetry and
          potential future use (e.g. writing a sidecar JSON file).
        - `timestamp`: reuse a caller-supplied stamp instead of generating
          one, so this port lands in the same acquisition folder as a
          sibling port configured for the same scan.

        One acquisition is one bounded context, so every file it produces
        (this device's data + any probe sidecar file, see
        `configure_field_data`) is written into a single acquisition folder
        `<dir>/YYYY-MM-DD_HHMMSS_stepScan_<name>/`, with files named
        `YYYY-MM-DD_HHMMSS_stepScan_<name>_<device>.csv` (device last).
        """
        # Resolve base directory
        if directory:
            dir_path = Path(directory)
            if not dir_path.is_absolute():
                dir_path = self.base_output_dir / dir_path
        else:
            # Use the base_output_dir directly when no directory is provided.
            dir_path = self.base_output_dir

        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_base = "".join(
            c for c in filename if c.isalnum() or c in ("-", "_")
        )

        acquisition_dir = dir_path / f"{timestamp}_stepScan_{safe_base}"
        acquisition_dir.mkdir(parents=True, exist_ok=True)

        self._dir_path = acquisition_dir
        self._timestamp = timestamp
        self._scan_name = safe_base
        self._configured_path = acquisition_dir / f"{timestamp}_stepScan_{safe_base}_aefi.csv"
        print(f"[CsvScanExportPort] CWD: {os.getcwd()}")
        print(f"[CsvScanExportPort] Configured export path (rel): {self._configured_path}")
        print(f"[CsvScanExportPort] Configured export path (abs): {self._configured_path.resolve()}")
        logger.debug("CSV export configured at %s", self._configured_path)

    def start(self) -> None:
        """
        Open the CSV file and prepare the writer.

        Header is written on the first call to `write_point`, when
        the field names are known from the first data dict.
        """
        if self._configured_path is None:
            raise RuntimeError("CsvScanExportPort.configure() must be called before start().")

        if self._file is not None:
            # Already started; nothing to do.
            return
        
        print(f"[CsvScanExportPort] Opening file for writing: {self._configured_path}")
        self._file = self._configured_path.open(mode="w", newline="", encoding="utf-8")
        # We initialise DictWriter without fieldnames; they will be set on first write.
        self._writer = csv.DictWriter(self._file, fieldnames=[])
        self._fieldnames = None

    def write_point(self, data: Dict[str, Any]) -> None:
        """
        Write a single data point to the CSV file.

        The first call uses the keys of `data` as column names and writes
        the header; subsequent calls reuse the same column order.
        """
        if self._file is None or self._writer is None:
            raise RuntimeError("CsvScanExportPort.start() must be called before write_point().")

        if self._fieldnames is None:
            # Establish a stable column order from the first data dict.
            self._fieldnames = list(data.keys())
            self._writer.fieldnames = self._fieldnames  # type: ignore[attr-defined]
            self._writer.writeheader()

        # Only keep known keys to avoid mismatches.
        row = {k: data.get(k, "") for k in self._fieldnames}
        self._writer.writerow(row)
        self._file.flush()
        # print(f"[CsvScanExportPort] Wrote point: {row.get('point_index', '?')}")

    def configure_field_data(self, n_components: int, probe_info: Dict[str, Any]) -> None:
        """
        Open a dedicated `<timestamp>_stepScan_<name>_<probe_label>.csv` file
        for electric field probe data — a separate file from the main
        aefi_device export, landing in the same acquisition folder.

        Must be called before `write_field_point()`. Header is written on the
        first call to `write_field_point`, from that row's own keys.
        """
        if self._dir_path is None or self._timestamp is None:
            raise RuntimeError("CsvScanExportPort.configure() must be called before configure_field_data().")

        probe_label = (probe_info or {}).get("probe_label", "field_probe")
        field_path = self._dir_path / f"{self._timestamp}_stepScan_{self._scan_name}_{probe_label}.csv"
        print(f"[CsvScanExportPort] Field data export path: {field_path}")
        self._field_file = field_path.open(mode="w", newline="", encoding="utf-8")
        self._field_writer = csv.DictWriter(self._field_file, fieldnames=[])
        self._field_fieldnames = None
        self._field_axis_labels = (probe_info or {}).get("axis_labels")

    def _component_column(self, prefix: str, i: int) -> str:
        """`field_x`/`field_std_dev_x` when the probe's axis_labels are known
        (e.g. Narda EP-601's X/Y/Z), else the generic `field_component_0`."""
        if self._field_axis_labels and i < len(self._field_axis_labels):
            return f"{prefix}_{self._field_axis_labels[i]}"
        return f"{prefix}_component_{i}"

    def write_field_point(self, data: Dict[str, Any]) -> None:
        """
        Write a single electric field measurement point to the sidecar CSV.

        Expects `field_components` (tuple) and `field_std_dev_components`
        (tuple or None), which are flattened into `field_component_0..N` /
        `field_std_dev_component_0..N` columns.
        """
        if self._field_file is None or self._field_writer is None:
            raise RuntimeError("CsvScanExportPort.configure_field_data() must be called before write_field_point().")

        row = {
            k: v for k, v in data.items()
            if k not in (
                "field_components", "field_std_dev_components",
                "baseline_field_components", "baseline_field_std_dev_components",
            )
        }
        for i, c in enumerate(data.get("field_components", ())):
            row[self._component_column("field", i)] = c
        std_devs = data.get("field_std_dev_components")
        if std_devs:
            for i, s in enumerate(std_devs):
                row[self._component_column("field_std_dev", i)] = s
        baseline_components = data.get("baseline_field_components")
        if baseline_components:
            for i, c in enumerate(baseline_components):
                row[self._component_column("baseline_field", i)] = c
        baseline_std_devs = data.get("baseline_field_std_dev_components")
        if baseline_std_devs:
            for i, s in enumerate(baseline_std_devs):
                row[self._component_column("baseline_field_std_dev", i)] = s

        if self._field_fieldnames is None:
            self._field_fieldnames = list(row.keys())
            self._field_writer.fieldnames = self._field_fieldnames  # type: ignore[attr-defined]
            self._field_writer.writeheader()

        out_row = {k: row.get(k, "") for k in self._field_fieldnames}
        self._field_writer.writerow(out_row)
        self._field_file.flush()

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """Write the acquisition's parameter snapshot as a JSON file in the
        acquisition folder: `<timestamp>_stepScan_<name>_acquisition-parameters.json`."""
        if self._dir_path is None or self._timestamp is None:
            raise RuntimeError("CsvScanExportPort.configure() must be called before write_metadata().")

        metadata_path = self._dir_path / f"{self._timestamp}_stepScan_{self._scan_name}_acquisition-parameters.json"
        with metadata_path.open(mode="w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

    def get_output_path(self) -> Optional[Path]:
        """Path to the main `_aefi.csv` file, once configured."""
        return self._configured_path

    def stop(self) -> None:
        """Close the CSV file(s) if open."""
        if self._file is not None:
            try:
                self._file.flush()
            finally:
                self._file.close()

        self._file = None
        self._writer = None
        self._fieldnames = None
        self._configured_path = None
        self._dir_path = None
        self._timestamp = None
        self._scan_name = None

        if self._field_file is not None:
            try:
                self._field_file.flush()
            finally:
                self._field_file.close()

        self._field_file = None
        self._field_writer = None
        self._field_fieldnames = None
        self._field_axis_labels = None


