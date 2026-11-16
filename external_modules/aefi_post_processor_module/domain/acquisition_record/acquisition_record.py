"""
AcquisitionRecord - One acquisition folder of the export, and whether its processed steps are up to date.
See acquisition_record_intention.md.
"""

from dataclasses import dataclass
from typing import Optional

NEW = 'new'
FORCED = 'forced'
SOURCE_NEWER = 'source_newer'


@dataclass
class AcquisitionRecord:
    name: str  # folder name: <timestamp>_<stepScan|flyScan>_<measured object>
    kind: str  # 'stepScan' or 'flyScan'
    folder: str  # the acquisition folder, designated by a string
    csv_file: str  # the device scan file of the folder (<name>_aefi.csv)
    acquisition_file: str  # the .h5 of the acquisition, where the processing steps are stored
    csv_modified_at: float  # seconds since the epoch
    steps_modified_at: Optional[float]  # None: the steps file does not exist yet

    def recalculation_reason(self, forced: bool = False) -> Optional[str]:
        """
        Why the steps must be computed again, or None when they are up to date.

        - NEW: no steps file yet
        - FORCED: the caller asked to process everything
        - SOURCE_NEWER: the scan file is not older than the steps file
        """
        if self.steps_modified_at is None:
            return NEW
        if forced:
            return FORCED
        if self.csv_modified_at >= self.steps_modified_at:
            return SOURCE_NEWER
        return None

    def needs_recalculation(self, forced: bool = False) -> bool:
        return self.recalculation_reason(forced) is not None
