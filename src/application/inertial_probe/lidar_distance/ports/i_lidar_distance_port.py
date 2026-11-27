"""
LIDAR Distance Port Interface: re-export of the published driver package.

The code lives in lidar_vl53l0x_esp32.ports.i_lidar_distance_port (LIDAR-VL53L0C-ESP32 repo, installed as a uv dependency
pinned to a tag). This module keeps its AEFI path so that existing imports keep
working. See i_lidar_distance_port_intention.md.
"""

from lidar_vl53l0x_esp32.ports.i_lidar_distance_port import (  # noqa: F401 — re-exported
    ILidarDistancePort as ILidarDistancePort,
)
