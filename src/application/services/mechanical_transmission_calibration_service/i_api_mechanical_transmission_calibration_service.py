from abc import ABC, abstractmethod
from typing import Optional

from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_calibration_dto import (
    MechanicalTransmissionCalibrationDTO,
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
        travel_per_motor_revolution_mm: float,
    ) -> None: ...

    @abstractmethod
    def get_current_calibration(self) -> Optional[MechanicalTransmissionCalibrationDTO]: ...
