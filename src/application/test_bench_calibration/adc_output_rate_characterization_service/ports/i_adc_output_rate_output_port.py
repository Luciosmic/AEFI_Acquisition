from abc import ABC, abstractmethod

from application.test_bench_calibration.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    AdcOutputRatePointDTO,
)


class IAdcOutputRateOutputPort(ABC):
    """
    Output Port for AdcOutputRateCharacterizationService — called from its
    background task: implementations must be thread-safe (Qt signals are).

    Responsibility:
        - `present_output_rate_step(message)`, `present_output_rate_point_measured(point)`,
          `present_output_rate_characterization_succeeded(result)`,
          `present_output_rate_characterization_failed(reason)`.

    Rationale:
        Un balayage des 16 OSR prend quelques dizaines de secondes, hors du thread
        UI. Sans port de sortie, l'opérateur ne verrait ni la progression, ni un OSR
        qui n'est pas appliqué (f_MOD implicite aberrante), ni la raison d'un échec
        (oscilloscope absent, lecture continue en cours).

    Design:
        - ABC pure, même patron que `IAcquisitionThroughputOutputPort` ; implémentée
          par `AdcOutputRateCharacterizationPresenter`, thread-safe (signaux Qt).
    """

    @abstractmethod
    def present_output_rate_step(self, message: str) -> None: ...

    @abstractmethod
    def present_output_rate_point_measured(self, point: AdcOutputRatePointDTO) -> None: ...

    @abstractmethod
    def present_output_rate_characterization_succeeded(self, result: AdcOutputRateCharacterizationDTO) -> None: ...

    @abstractmethod
    def present_output_rate_characterization_failed(self, reason: str) -> None: ...
