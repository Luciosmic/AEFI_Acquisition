"""
Bar Transmission Calibration DTOs

See bar_transmission_calibration_dtos_intention.md.

Units: increments are motor increments (pulses counted by the controller);
distances in mm (UCUM `mm`), durations in s (UCUM `s`), speeds in
increments/s.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

# Initial values, to be adjusted on the bench (decision 2026-10-15: tunable from the UI).
# Settling after a stop: the column must stop swinging before the LIDAR is read.
DEFAULT_SETTLE_TIME_S = 0.5
# k samples per point at rest: 10 samples = 0.4 s at the 25 Hz LIDAR stream.
DEFAULT_SAMPLES_PER_POINT = 10
# k_σ of the undecidable zone |d̄ − s| < k_σ·σ/√k.
DEFAULT_K_SIGMA = 3.0
# Fly scan speed: the "slow" preset (HS 800 Hz) — at 25 Hz, one LIDAR point
# every 32 increments (~0.7 mm at 21.8 µm/increment).
DEFAULT_FLY_SPEED_INCREMENTS_PER_S = 800
# Margin v·τ around each coarse front: τ covers the LIDAR latency, one sample
# period and the position read latency, with room to spare.
DEFAULT_COARSE_MARGIN_S = 0.5


@dataclass(frozen=True)
class BarCalibrationSettingsDTO:
    """Operator-tunable settings of one axis measurement."""

    settle_time_s: float = DEFAULT_SETTLE_TIME_S
    samples_per_point: int = DEFAULT_SAMPLES_PER_POINT
    k_sigma: float = DEFAULT_K_SIGMA
    fly_speed_increments_per_s: int = DEFAULT_FLY_SPEED_INCREMENTS_PER_S
    coarse_margin_s: float = DEFAULT_COARSE_MARGIN_S


@dataclass(frozen=True)
class LidarDistanceReading:
    """One LIDAR distance, timestamped at its reception on the PC (s, same clock as the service)."""

    timestamp_s: float
    distance_mm: float


@dataclass(frozen=True)
class EdgeBracketDTO:
    on_bar_increment: int
    off_bar_increment: int
    limited_by_lidar_noise: bool  # an undecidable zone bounded the refinement, not the motor
    center_increment: float
    half_width_increments: float


@dataclass(frozen=True)
class AxisBarTransmissionDTO:
    """One axis measured: brackets, N ± δ, transmission ± uncertainty, and the
    plateaus/threshold the refinement relied on."""

    axis: str
    bar_length_mm: float
    bar_length_uncertainty_mm: float
    first_front: EdgeBracketDTO
    second_front: EdgeBracketDTO
    full_steps_per_revolution: float
    microsteps: int
    increments_between_fronts: float
    increments_uncertainty: float
    travel_per_motor_revolution_mm: float
    travel_per_motor_revolution_uncertainty_mm: float
    relative_uncertainty: float
    microns_per_pulse: float
    on_bar_distance_mm: float
    off_bar_distance_mm: float
    threshold_mm: float
    plateau_noise_mm: float
    measured_at: datetime


@dataclass(frozen=True)
class BarTransmissionMeanDTO:
    """X and Y combined: the value to record, and the deviation shown to the operator."""

    x_travel_per_motor_revolution_mm: float
    y_travel_per_motor_revolution_mm: float
    travel_per_motor_revolution_mm: float
    travel_per_motor_revolution_uncertainty_mm: float
    deviation_mm: float
    relative_deviation: float
    axes_agree: bool
    entry_id: Optional[UUID] = None  # set once recorded
