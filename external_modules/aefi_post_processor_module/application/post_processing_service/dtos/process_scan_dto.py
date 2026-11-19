from dataclasses import dataclass
from typing import Optional, Tuple

from ....domain.processing.processing_steps.processing_steps import ProcessingParameters


@dataclass(frozen=True)
class ProcessScanDTO:
    """One processing request: which scan file to read, where the steps of its acquisition go, how to process."""

    csv_path: str
    acquisition_file: str
    parameters: ProcessingParameters = ProcessingParameters()
    skip_interpolation: bool = False
    # The angles (degrees) the acquisition applied, read from its parameters file: they replace
    # `parameters.rotation_angles`. None: the file does not give any, the requested angles stay.
    applied_rotation_angles: Optional[Tuple[float, float, float]] = None
