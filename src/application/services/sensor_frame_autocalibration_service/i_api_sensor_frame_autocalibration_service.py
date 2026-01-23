"""
Application: Sensor Frame Autocalibration API Interface

Rationale (global context)
    Primary adapters (UI / CLI / HTTP) must interact with the program through a stable
    inbound Application API, without depending on internal use-case implementations.

Responsibility (local context, promise theory)
    This interface defines the public operations for sensor-frame autocalibration:
    given measurement batches acquired under X excitation and Y excitation, compute
    the best sensor rotation angles and apply them to the transformation state.

Design (tactical choices)
    - `i_api_*` naming to avoid confusion with outbound infrastructure ports.
    - Pure interface (ABC) consumed by primary adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class IApiSensorFrameAutocalibrationService(ABC):
    """Inbound Application API for sensor-frame autocalibration."""

    @abstractmethod
    def calibrate_from_measurements(
        self,
        x_measurements: List[VoltageMeasurement],
        y_measurements: List[VoltageMeasurement],
        initial_angles: Optional[Tuple[float, float, float]] = None,
    ) -> Tuple[float, float, float]:
        """
        Calibrate sensor frame rotation angles from measurement data.

        Args:
            x_measurements: List of measurements with X_DIR excitation
            y_measurements: List of measurements with Y_DIR excitation
            initial_angles: Optional initial guess (theta_x, theta_y, theta_z) in degrees

        Returns:
            Optimized angles (theta_x, theta_y, theta_z) in degrees
        """
        raise NotImplementedError

