from dataclasses import dataclass
from datetime import datetime
from typing import Optional

PROCESSED = 'processed'
TO_RECOMPUTE = 'to_recompute'
FAILED = 'failed'


@dataclass(frozen=True)
class AcquisitionStatusDTO:
    """One acquisition of the export with its processing state: PROCESSED, TO_RECOMPUTE or FAILED."""

    name: str
    kind: str
    folder: str
    csv_file: str
    acquisition_file: str
    state: str
    reason: Optional[str] = None  # why it is to recompute: new, forced or source_newer
    failure_message: Optional[str] = None  # the message of the failure remembered for this session
    # What identifies the acquisition, from its parameters file (None: not said) and where it is filed.
    group: str = ""
    acquired_at: Optional[datetime] = None
    measured_object: Optional[str] = None
    lift_off_mm: Optional[float] = None
