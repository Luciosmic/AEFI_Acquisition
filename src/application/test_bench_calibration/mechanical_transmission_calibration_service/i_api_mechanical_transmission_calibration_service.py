from abc import ABC, abstractmethod
from typing import Optional

from application.test_bench_calibration.mechanical_transmission_calibration_service.dtos.mechanical_transmission_calibration_dto import (
    MechanicalTransmissionCalibrationDTO,
)
from application.test_bench_calibration.mechanical_transmission_calibration_service.dtos.mechanical_transmission_gap_dto import (
    MechanicalTransmissionGapDTO,
)


class IApiMechanicalTransmissionCalibrationService(ABC):
    """
    Responsibility:
    - Inbound API contract for MechanicalTransmissionCalibrationService.

    Rationale:
    - Callers (composition root, export, a future panel) depend on this
      contract, not on the concrete service.

    Design:
    - Pure ABC, no state.
    """

    @abstractmethod
    def record_calibration(
        self,
        microsteps: int,
        driver_current_a: float,
        driver_peak_current_a: float,
        microns_per_pulse: float,
    ) -> None: ...

    @abstractmethod
    def get_current_calibration(self) -> Optional[MechanicalTransmissionCalibrationDTO]: ...

    @abstractmethod
    def get_current_gap(self) -> Optional[MechanicalTransmissionGapDTO]: ...
