"""
LIDAR Distance Value Object

See lidar_distance_intention.md.
"""

import math
from dataclasses import dataclass
from typing import Optional

# Raw value the LIDAR sends when it measures nothing (no return).
NO_RETURN_RAW = 0


@dataclass(frozen=True)
class LidarDistance:
    """One LIDAR sample: a valid return with its distance (mm, always > 0), or no return.

    `distance_mm` is None for "no return"; a distance of 0 does not exist."""

    distance_mm: Optional[float]

    def __post_init__(self) -> None:
        if self.distance_mm is not None and not (math.isfinite(self.distance_mm) and self.distance_mm > 0):
            raise ValueError(f"a valid LIDAR distance is finite and > 0 mm, got {self.distance_mm}")

    @staticmethod
    def from_raw(raw: int, mm_per_lsb: float) -> "LidarDistance":
        """From the sensor's raw integer: NO_RETURN_RAW (0) means "no return", not
        "distance 0"; a negative raw is not a distance either. `mm_per_lsb`: the
        sensor conversion factor, owned by the adapter."""
        if not (math.isfinite(mm_per_lsb) and mm_per_lsb > 0):
            raise ValueError(f"mm_per_lsb must be finite and > 0, got {mm_per_lsb}")
        if raw <= NO_RETURN_RAW:
            return LidarDistance.no_return()
        return LidarDistance(raw * mm_per_lsb)

    @staticmethod
    def no_return() -> "LidarDistance":
        return LidarDistance(None)

    @property
    def has_return(self) -> bool:
        return self.distance_mm is not None
