"""
Bar Transmission Calibration Output Port

Responsibility:
- Tell the presenter how a running axis measurement progresses, and how it
  ends (measured or failed).
- Hand over, as they happen, the data the operator checks the measurement on:
  fly scan profile points, coarse localization (threshold, fronts), points read
  at rest and the current bracket of each front.

Rationale:
- measure_axis runs in the background (minutes on the bench): its outcome
  cannot be a return value.

Design:
- Called from the background task: the implementation must only hand the
  data over to its UI thread (Qt signals), never touch widgets.
- Profile points come in small batches (one per loop turn of the fly scan,
  ~10 Hz); limiting the redraw rate is the display's job.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
    CoarseLocalizationDTO,
    FrontBracketDTO,
    ProfilePointDTO,
    RestPointDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarTransmissionCalibrationError,
)


class IBarTransmissionCalibrationOutputPort(ABC):
    @abstractmethod
    def present_measurement_progress(self, axis: str, message: str) -> None: ...

    @abstractmethod
    def present_profile_points(self, axis: str, points: Sequence[ProfilePointDTO]) -> None: ...

    @abstractmethod
    def present_coarse_localization(self, axis: str, located: CoarseLocalizationDTO) -> None: ...

    @abstractmethod
    def present_rest_point(self, axis: str, point: RestPointDTO) -> None: ...

    @abstractmethod
    def present_front_bracket(self, axis: str, bracket: FrontBracketDTO) -> None: ...

    @abstractmethod
    def present_axis_measured(self, result: AxisBarTransmissionDTO) -> None: ...

    @abstractmethod
    def present_axis_failed(self, axis: str, error: BarTransmissionCalibrationError) -> None: ...
