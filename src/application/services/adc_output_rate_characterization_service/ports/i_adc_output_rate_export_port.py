from abc import ABC, abstractmethod
from typing import Sequence, Tuple

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    DrdyCaptureDTO,
)
from domain.shared_kernel.operation_result import OperationResult


class IAdcOutputRateExportPort(ABC):
    """
    Responsibility:
    - Persist one ODR characterization: summary per OSR, every DRDY interval,
      and the raw waveforms.

    Rationale:
    - The ODR must stay re-computable from the raw capture (another interval
      rule, another threshold), like every other characterization.

    Design:
    - `captures` are (OSR, capture) pairs in measurement order.
    - Expected I/O failures are failures, never raised. Returns the location.
    """

    @abstractmethod
    def export(
        self,
        result: AdcOutputRateCharacterizationDTO,
        captures: Sequence[Tuple[int, DrdyCaptureDTO]],
    ) -> OperationResult[str, str]: ...
