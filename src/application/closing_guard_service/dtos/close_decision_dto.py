from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class OpenAcquisitionDTO:
    """An acquisition whose export is open: what to name to the operator."""

    acquisition_kind: str
    acquisition_id: str
    measured_object: str = ""


@dataclass(frozen=True)
class CloseDecisionDTO:
    """Whether the application may close now; when not, the acquisitions still exporting."""

    allowed: bool
    open_acquisitions: Tuple[OpenAcquisitionDTO, ...] = ()
