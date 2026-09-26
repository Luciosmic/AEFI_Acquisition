from abc import ABC, abstractmethod
from typing import Optional

from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import (
    ActiveSensorRotationDTO,
    SensorCalibrationDTO,
)


class IApiSensorCalibrationService(ABC):
    """
    Responsibility:
    - Inbound API contract for SensorCalibrationService.
    - Defines what UI adapters and presenters may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound ports
      (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by SensorCalibrationService.
    """

    @abstractmethod
    def record_calibration(
        self,
        theta_x_degrees: float,
        theta_y_degrees: float,
        theta_z_degrees: float,
    ) -> None: ...

    @abstractmethod
    def preview_rotation(
        self,
        theta_x_degrees: float,
        theta_y_degrees: float,
        theta_z_degrees: float,
    ) -> None: ...

    @abstractmethod
    def reset_to_default(self) -> None: ...

    @abstractmethod
    def get_latest_calibration(self) -> Optional[SensorCalibrationDTO]: ...

    @abstractmethod
    def get_active_rotation(self) -> ActiveSensorRotationDTO: ...
