from abc import ABC, abstractmethod

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    AdcOutputRatePointDTO,
)


class IAdcOutputRateOutputPort(ABC):
    """
    Output Port for AdcOutputRateCharacterizationService — called from its
    background task: implementations must be thread-safe (Qt signals are).
    """

    @abstractmethod
    def present_output_rate_step(self, message: str) -> None: ...

    @abstractmethod
    def present_output_rate_point_measured(self, point: AdcOutputRatePointDTO) -> None: ...

    @abstractmethod
    def present_output_rate_characterization_succeeded(self, result: AdcOutputRateCharacterizationDTO) -> None: ...

    @abstractmethod
    def present_output_rate_characterization_failed(self, reason: str) -> None: ...
