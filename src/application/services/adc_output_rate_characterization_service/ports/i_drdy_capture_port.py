from abc import ABC, abstractmethod

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    DrdyCaptureDTO,
    DrdyCaptureRequestDTO,
)
from domain.shared_kernel.operation_result import OperationResult


class IDrdyCapturePort(ABC):
    """
    Responsibility:
    - Capture the DRDY pin of the ADC on an oscilloscope channel and return
      the instants of its falling edges (one per conversion).

    Rationale:
    - The ODR is only known without assumption from DRDY; the use case must
      not know the instrument (VISA address, SCPI commands, timebase steps).

    Design:
    - The adapter leaves the instrument as it found it (setup saved and
      restored around the capture).
    - No instrument, no edge, communication error: OperationResult.fail with
      a readable reason — never raised.
    """

    @abstractmethod
    def capture_falling_edges(self, request: DrdyCaptureRequestDTO) -> OperationResult[DrdyCaptureDTO, str]: ...
