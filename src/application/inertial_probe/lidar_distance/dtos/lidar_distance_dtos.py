"""
LIDAR Distance DTOs

See lidar_distance_dtos_intention.md.

Units: distances in mm (UCUM `mm`), timestamps in s (UCUM `s`).
"""

from dataclasses import dataclass

from domain.lidar.lidar_distance.lidar_distance import LidarDistance


@dataclass(frozen=True)
class LidarDistanceReading:
    """One LIDAR sample (a valid return or no return, see LidarDistance),
    timestamped at its reception on the PC (s, same clock as the service)."""

    timestamp_s: float
    distance: LidarDistance
