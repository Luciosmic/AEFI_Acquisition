"""
Post-Processing Port Interface

Responsibility:
- Define the contract for turning a scan's raw CSV export into its own
  HDF5 file (the raw points re-read from the CSV, the processing steps and
  their provenance) and opening the result in the visualization app.

Rationale:
- Keeps `ScanExportService` decoupled from the external_modules post
  processor: it only knows "run post-processing for this CSV",
  not how that pipeline works.
- The acquisition exports the CSV only: the HDF5 file does not exist before
  post-processing, which creates it where its catalog looks for it.

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
    def run(self, csv_path: Path) -> None:
        """Process `csv_path` into the HDF5 file of its acquisition folder,
        then open the result in the visualization app."""
        pass
