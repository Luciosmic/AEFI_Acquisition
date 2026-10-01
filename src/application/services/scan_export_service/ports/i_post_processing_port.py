"""
Post-Processing Port Interface

Responsibility:
- Define the contract for turning a scan's raw CSV export into the
  processed HDF5 steps (preprocessing, phase calibration, amplitude
  subtraction, frame rotation, interpolation) and opening the result in
  the visualization app.

Rationale:
- Keeps `ScanExportService` decoupled from the external_modules post
  processor: it only knows "run post-processing for these two files",
  not how that pipeline works.

Design:
- Infrastructure implements this by driving
  `external_modules/aefi_post_processor_module` in-process for the
  processing part, then spawning a separate OS process for the Qt
  visualization app (a second QApplication cannot run inside this one).
"""

from abc import ABC, abstractmethod
from pathlib import Path


class IPostProcessingPort(ABC):
    """Interface for triggering post-processing + visualization after a scan."""

    @abstractmethod
    def run(self, csv_path: Path, hdf5_path: Path) -> None:
        """Process `csv_path` into `hdf5_path`'s HDF5 steps, then open the
        result in the visualization app."""
        pass
