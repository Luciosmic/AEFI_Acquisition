from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AcquisitionProvenanceDTO:
    """What the acquisition recorded about the scan file in its parameters file: the activity that produced it and the
    SHA-256 it took of the CSV when it closed. Either is None when the file does not say."""

    activity_id: Optional[str]
    declared_csv_sha256: Optional[str]
