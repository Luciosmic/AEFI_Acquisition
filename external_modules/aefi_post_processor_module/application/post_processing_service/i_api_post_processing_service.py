from abc import ABC, abstractmethod

from .dtos.process_scan_dto import ProcessScanDTO
from .dtos.processing_summary_dto import ProcessingSummaryDTO


class IApiPostProcessingService(ABC):
    """
    Responsibility:
    - Inbound contract of the post-processing use case: turn a scan file into the five stored steps.

    Rationale:
    - Callers (the raccord for the acquisition, later the Acquisitions panel) depend on this contract, never on the concrete service.

    Design:
    - Pure ABC. A failed step raises after being logged, with the original exception carrying the name of the step in `processing_step`; nothing is hidden in the summary. Implemented by PostProcessingService.
    """

    @abstractmethod
    def process_scan(self, request: ProcessScanDTO) -> ProcessingSummaryDTO:
        """Read the scan, compute preprocessed, phase_calibrated, amplitude_subtracted, rotated_frame and interpolated, store each."""
