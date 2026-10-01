from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


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
    angles. `mounting_matrix` is P itself (rows, columns = sensor axes in the
    sources frame), computed by the domain so no consumer re-derives the
    convention from the angles."""

    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    is_calibrated: bool
    is_trial: bool
    recorded_at: Optional[datetime]
    mounting_matrix: Tuple[Tuple[float, float, float], ...]


@dataclass(frozen=True)
class AutomaticSensorCalibrationDTO:
    """Mounting angles fitted by the automatic calibration (applied as a
    trial, not recorded) and the fit quality: residual misalignment of the
    corrected X/Y responses from +e_x/+e_y, and the angle between the raw
    X and Y responses (ideally 90°)."""

    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    misalignment_x_degrees: float
    misalignment_y_degrees: float
    response_separation_degrees: float
