"""
LidarDistance value object: re-export of the published driver package.

The code lives in lidar_vl53l0x_esp32.lidar_distance (LIDAR-VL53L0C-ESP32 repo, installed as a uv dependency
pinned to a tag). This module keeps its AEFI path so that existing imports keep
working. See lidar_distance_intention.md.
"""

from lidar_vl53l0x_esp32.lidar_distance import (  # noqa: F401 — re-exported
    LidarDistance as LidarDistance,
)
