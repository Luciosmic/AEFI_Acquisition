"""LSB -> physical units for the LSM9DS1 board (pure, no I/O).

Formula (same as the LabVIEW VI): raw * full_scale / 2**15.
Full scales: see lsm9ds1_conversion_intention.md (gyroscope and magnetometer
still unverified).
"""

from typing import Iterable, Tuple

# ponytail: accelerometer 2 g deduced (the VI announces 4 g but |a| at rest came out
# 2.07 g with it); gyroscope 490 dps copied from a VI without verification;
# magnetometer 400 uT assumes divisor 2**15 (2**16 would halve it, undecided).
# Ceiling: gyroscope and magnetometer values are shown flagged "not verified".
# Upgrade: confirm against datasheet DS10724 and a known rotation / field.
ACCELEROMETER_FULL_SCALE_G = 2
GYROSCOPE_FULL_SCALE_DPS = 490
MAGNETOMETER_FULL_SCALE_UT = 400

LSB_HALF_RANGE = 2**15

# ponytail: lidar raw value is in millimetres according to the user (not measured by
# us); plausible order of magnitude (~1.27 m). Factor and offset unverified.
# The lidar is a distance, not an inertial quantity: it is converted here only
# because it travels in the same stream. Ceiling: one stream carries both.
# Upgrade: separate lidar port; verify against 3 known distances.
LIDAR_MM_PER_LSB = 1.0


def lidar_raw_to_mm(raw: int) -> float:
    """Single conversion point for the lidar: raw -> millimetres."""
    return raw * LIDAR_MM_PER_LSB


def raw_to_physical(raw: Iterable[int], full_scale: float) -> Tuple[float, ...]:
    return tuple(v * full_scale / LSB_HALF_RANGE for v in raw)
