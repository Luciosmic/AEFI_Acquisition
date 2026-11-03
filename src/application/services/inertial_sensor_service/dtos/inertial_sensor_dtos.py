"""
Inertial sensor DTOs

Responsibility:
- InertialSensorStreamSample: one streamed line, timestamped on the PC, in
  physical units (g, deg/s, uT, mm).
- InertialSensorAcquisitionConfig: channels requested for an acquisition.

Units (UCUM): acceleration `[g]`, angular rate `deg/s`, magnetic field `uT`,
lidar distance `mm`.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

Vector3 = Tuple[float, float, float]

ACCELEROMETER_CHANNEL = "accelerometer"
GYROSCOPE_CHANNEL = "gyroscope"
MAGNETOMETER_CHANNEL = "magnetometer"
# ponytail: the lidar measures a distance, it is not an inertial sensor. It is a
# channel of the same stream only because it sits on the same board/serial link
# (an infrastructure fact). Ceiling: one stream carries both. Upgrade: a separate
# lidar concept and port; the shared board stays an infrastructure detail.
LIDAR_CHANNEL = "lidar"

ALL_CHANNELS: Tuple[str, ...] = (
    ACCELEROMETER_CHANNEL,
    GYROSCOPE_CHANNEL,
    MAGNETOMETER_CHANNEL,
    LIDAR_CHANNEL,
)


@dataclass(frozen=True)
class InertialSensorStreamSample:
    """One streamed line, timestamped on the PC at reception (perf_counter seconds).

    Every channel is optional: the stream may carry only a subset.
    """

    timestamp_s: float
    acceleration_g: Optional[Vector3] = None
    angular_rate_dps: Optional[Vector3] = None
    magnetic_field_ut: Optional[Vector3] = None
    # ponytail: lidar fields in the inertial sensor sample (see LIDAR_CHANNEL).
    lidar_raw: Optional[int] = None  # integer as received from the board
    lidar_distance_mm: Optional[float] = None  # unit given by the user, unverified


@dataclass(frozen=True)
class InertialSensorAcquisitionConfig:
    """Channels requested for one acquisition (default: all four)."""

    channels: Tuple[str, ...] = ALL_CHANNELS
