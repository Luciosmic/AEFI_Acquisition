"""
Application: Sensor Frame Autocalibration API Service (Implementation)

Rationale (global context)
    Provide an inbound Application API consumed by primary adapters while keeping
    the internal use-case (`SensorFrameAutocalibrationService`) encapsulated.

Responsibility (local context, promise theory)
    Implements `IApiSensorFrameAutocalibrationService` by delegating to the use-case.
    This class does not implement optimization; it orchestrates the call and the
    side-effect (updating `TransformationService`) remains inside the use-case.

Design (tactical choices)
    - Thin adapter over `SensorFrameAutocalibrationService`.
    - Dependency injection via constructor.
"""

from typing import List, Tuple, Optional

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement

from application.services.sensor_frame_autocalibration_service.i_api_sensor_frame_autocalibration_service import (
    IApiSensorFrameAutocalibrationService,
)
from application.services.sensor_frame_autocalibration_service.sensor_frame_autocalibration_service import (
    SensorFrameAutocalibrationService,
)


class SensorFrameAutocalibrationApiService(IApiSensorFrameAutocalibrationService):
    """Inbound API implementation for sensor-frame autocalibration."""

    def __init__(self, use_case: SensorFrameAutocalibrationService) -> None:
        self._use_case = use_case

    def calibrate_from_measurements(
        self,
        x_measurements: List[VoltageMeasurement],
        y_measurements: List[VoltageMeasurement],
        initial_angles: Optional[Tuple[float, float, float]] = None,
    ) -> Tuple[float, float, float]:
        return self._use_case.calibrate_from_measurements(
            x_measurements=x_measurements,
            y_measurements=y_measurements,
            initial_angles=initial_angles,
        )

