from abc import ABC, abstractmethod
from typing import Tuple

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateRequestDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_output_port import (
    IAdcOutputRateOutputPort,
)


class IApiAdcOutputRateCharacterizationService(ABC):
    """
    Responsibility:
    - Inbound API contract for AdcOutputRateCharacterizationService
      (presenter -> application). Outcome through the output port.
    """

    @abstractmethod
    def set_output_port(self, output_port: IAdcOutputRateOutputPort) -> None: ...

    @abstractmethod
    def start_characterization(self, request: AdcOutputRateRequestDTO) -> None: ...

    @abstractmethod
    def get_allowed_oversampling_ratios(self) -> Tuple[int, ...]: ...
