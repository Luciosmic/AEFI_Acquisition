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
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, TextIO

from src.application.services.scan_application_service.ports.i_scan_export_port import (
    IScanExportPort,
)


logger = logging.getLogger(__name__)


@dataclass
class CsvScanExportPort(IScanExportPort):
    """
    CSV-based implementation of `IExportPort`.

    Notes:
    - By default, files are written under a `data_repository` directory
      at the project root (configurable via `directory` in `configure`).
    - The caller is responsible for providing a flat `data` dict with
      scalar values in `write_point`.
    """

    # Base directory used when `directory` passed to `configure` is relative or empty.
    base_output_dir: Path = field(
        default_factory=lambda: Path("data_repository")
    )

    _file: Optional[TextIO] = field(init=False, default=None)
    _writer: Optional[csv.DictWriter] = field(init=False, default=None)
    _fieldnames: Optional[List[str]] = field(init=False, default=None)
    _configured_path: Optional[Path] = field(init=False, default=None)

    def configure(
        self, directory: str, filename: str, metadata: Dict[str, Any]
    ) -> None:
        """
        Configure the export destination and filename.

        - `directory`: if absolute, used as-is; if relative or empty, it is
          resolved under `base_output_dir`.
        - `filename`: logical base name (without date/time and extension);
          a timestamped filename of the form
          `YYYY-MM-DD_HHMMSS_<filename>.csv` is generated.
        - `metadata`: currently unused here but kept for API symmetry and
          potential future use (e.g. writing a sidecar JSON file).
        """
        # Resolve base directory
        if directory:
            dir_path = Path(directory)
            if not dir_path.is_absolute():
                dir_path = self.base_output_dir / dir_path
        else:
            # Use the base_output_dir directly when no directory is provided.
            dir_path = self.base_output_dir

        dir_path.mkdir(parents=True, exist_ok=True)

        # Build timestamped filename to respect export naming convention.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_base = "".join(
            c for c in filename if c.isalnum() or c in ("-", "_")
        )
        final_name = f"{timestamp}_{safe_base}.csv"

        self._configured_path = dir_path / final_name
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

    def stop(self) -> None:
        """Close the CSV file if it is open."""
        if self._file is not None:
            try:
                self._file.flush()
            finally:
                self._file.close()

        self._file = None
        self._writer = None
        self._fieldnames = None
        self._configured_path = None


