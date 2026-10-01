from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SensorCalibrationDTO:
    """Latest recorded mounting-angle calibration for the current sensor
    mounting and source geometry entry — primitives only, no domain VO
    crosses the application -> interface boundary."""

    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    recorded_at: datetime


@dataclass(frozen=True)
class ActiveSensorRotationDTO:
    """Mounting angles P (brings the sensor from the sources frame to its
    current mounting; measurement E_sensor = Pᵀ·E_sources; correction
    E_sources = P·E_sensor) currently applied to sensor readings: trial angles being tuned, else the latest calibration for the
    current sensor mounting and source geometry, else the ideal default
    angles."""

    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    is_calibrated: bool
    is_trial: bool
    recorded_at: Optional[datetime]
