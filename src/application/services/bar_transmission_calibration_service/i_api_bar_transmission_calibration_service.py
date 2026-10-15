"""
Inbound API of BarTransmissionCalibrationService (use cases exposed to the presenter).
"""

from abc import ABC, abstractmethod

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
    BarCalibrationSettingsDTO,
    BarTransmissionMeanDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarTransmissionCalibrationError,
)
from application.services.bar_transmission_calibration_service.ports.i_bar_transmission_calibration_output_port import (
    IBarTransmissionCalibrationOutputPort,
)
from domain.shared_kernel.operation_result import OperationResult


class IApiBarTransmissionCalibrationService(ABC):
    # -- commands -----------------------------------------------------------------

    @abstractmethod
    def set_output_port(self, output_port: IBarTransmissionCalibrationOutputPort) -> None: ...

    @abstractmethod
    def measure_axis(
        self,
        axis: str,
        bar_length_mm: float,
        bar_length_uncertainty_mm: float,
        settings: BarCalibrationSettingsDTO,
    ) -> OperationResult[None, BarTransmissionCalibrationError]:
        """Start measuring one axis in the background (outcome through the output
        port); refused at once (typed) when it cannot start."""

    @abstractmethod
    def cancel_measurement(self) -> None:
        """Ask the running measurement to stop the axis and give up."""

    @abstractmethod
    def record(
        self, x: AxisBarTransmissionDTO, y: AxisBarTransmissionDTO
    ) -> OperationResult[BarTransmissionMeanDTO, BarTransmissionCalibrationError]:
        """Record the X/Y mean as a new mechanical transmission entry (operator click only)."""

    # -- queries ------------------------------------------------------------------

    @abstractmethod
    def default_settings(self) -> BarCalibrationSettingsDTO: ...

    @abstractmethod
    def is_measuring(self) -> bool: ...

    @abstractmethod
    def compare(
        self, x: AxisBarTransmissionDTO, y: AxisBarTransmissionDTO
    ) -> OperationResult[BarTransmissionMeanDTO, BarTransmissionCalibrationError]:
        """X/Y mean and deviation, without recording anything."""
