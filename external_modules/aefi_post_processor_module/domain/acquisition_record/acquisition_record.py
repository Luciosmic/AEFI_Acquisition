"""
AcquisitionRecord - One acquisition folder of the export, and whether its processed steps are up to date.
See acquisition_record_intention.md.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .value_objects.applied_rotation.applied_rotation import AppliedRotation

NEW = 'new'
INCOMPLETE = 'incomplete'
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
    steps_hold_preprocessed: bool  # the steps file holds the first step: a processing that failed early leaves it empty
    # What the acquisition says of itself in its parameters file (None: not said), and where the operator filed it.
    group: str = ""  # the folder holding the acquisition folder, relative to the export ("" at its root)
    acquired_at: Optional[datetime] = None
    measured_object: Optional[str] = None
    lift_off_mm: Optional[float] = None
    # The rotation the acquisition applied, when its parameters file gives one the post-processing can use;
    # `rotation_problem` says why not when it gives one that cannot be used (None: nothing to say).
    applied_rotation: Optional[AppliedRotation] = None
    rotation_problem: Optional[str] = None
    schema_version: Optional[str] = None

    def recalculation_reason(self, forced: bool = False) -> Optional[str]:
        """
        Why the steps must be computed again, or None when they are up to date.

        - NEW: no steps file yet
        - INCOMPLETE: the steps file exists but holds no `preprocessed` step (a processing failed before storing it)
        - FORCED: the caller asked to process everything
        - SOURCE_NEWER: the scan file is not older than the steps file
        """
        if self.steps_modified_at is None:
            return NEW
        if not self.steps_hold_preprocessed:
            return INCOMPLETE
        if forced:
            return FORCED
        if self.csv_modified_at >= self.steps_modified_at:
            return SOURCE_NEWER
        return None

    def needs_recalculation(self, forced: bool = False) -> bool:
        return self.recalculation_reason(forced) is not None
