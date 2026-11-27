"""
ESP32 serial LIDAR adapter: re-export of the published driver package.

The code lives in lidar_vl53l0x_esp32.adapter_lidar_distance_port (LIDAR-VL53L0C-ESP32 repo, installed as a uv dependency
pinned to a tag). This module keeps its AEFI path so that existing imports keep
working. See esp32_serial_lidar_intention.md.
"""

from lidar_vl53l0x_esp32.adapter_lidar_distance_port import (  # noqa: F401 — re-exported
    Esp32SerialLidarAdapter as Esp32SerialLidarAdapter,
    MAX_CONSECUTIVE_READ_ERRORS as MAX_CONSECUTIVE_READ_ERRORS,
    MAX_LINE_BYTES as MAX_LINE_BYTES,
    MM_PER_LSB as MM_PER_LSB,
    READ_TIMEOUT_S as READ_TIMEOUT_S,
    parse_raw_distance as parse_raw_distance,
)
