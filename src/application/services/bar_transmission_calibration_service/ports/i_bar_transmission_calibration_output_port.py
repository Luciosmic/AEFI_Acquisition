"""
Bar Transmission Calibration Output Port

Responsibility:
- Tell the presenter how a running axis measurement progresses, and how it
  ends (measured or failed).

Rationale:
- measure_axis runs in the background (minutes on the bench): its outcome
  cannot be a return value.

Design:
- Called from the background task: the implementation must only hand the
  data over to its UI thread (Qt signals), never touch widgets.
"""

from abc import ABC, abstractmethod

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarTransmissionCalibrationError,
)


class IBarTransmissionCalibrationOutputPort(ABC):
    @abstractmethod
    def present_measurement_progress(self, axis: str, message: str) -> None: ...

    @abstractmethod
    def present_axis_measured(self, result: AxisBarTransmissionDTO) -> None: ...

    @abstractmethod
    def present_axis_failed(self, axis: str, error: BarTransmissionCalibrationError) -> None: ...
