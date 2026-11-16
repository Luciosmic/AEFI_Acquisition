from dataclasses import dataclass

from ....domain.processing.processing_steps.processing_steps import ProcessingParameters


@dataclass(frozen=True)
class ProcessScanDTO:
    """One processing request: which scan file to read, where the steps of its acquisition go, how to process."""

    csv_path: str
    acquisition_file: str
    parameters: ProcessingParameters = ProcessingParameters()
    skip_interpolation: bool = False
