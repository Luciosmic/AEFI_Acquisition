"""
LIDAR distance DTOs: re-export of the published driver package.

The code lives in lidar_vl53l0x_esp32.ports.lidar_distance_dtos (LIDAR-VL53L0C-ESP32 repo, installed as a uv dependency
pinned to a tag). This module keeps its AEFI path so that existing imports keep
working. See lidar_distance_dtos_intention.md.
"""

from lidar_vl53l0x_esp32.ports.lidar_distance_dtos import (  # noqa: F401 — re-exported
    LidarDistanceReading as LidarDistanceReading,
)
