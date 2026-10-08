from abc import ABC, abstractmethod

from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import (
    AutomaticSensorCalibrationDTO,
)


class ISensorCalibrationOutputPort(ABC):
    """
    Output Port for SensorCalibrationService — see
    i_sensor_calibration_output_port_intention.md.

    Called from the automatic calibration's background task: implementations
    must be thread-safe (Qt signals are).
    """

    @abstractmethod
    def present_automatic_calibration_step(self, message: str) -> None: ...

    @abstractmethod
    def present_automatic_calibration_succeeded(self, result: AutomaticSensorCalibrationDTO) -> None: ...

    @abstractmethod
    def present_automatic_calibration_failed(self, reason: str) -> None: ...
