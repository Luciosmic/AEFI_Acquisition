"""
LSM9DS1 inertial sensor stream adapter

Responsibility:
- Implement IInertialSensorStreamPort over LSM9DS1StreamDriver and the
  LSB -> physical units conversion.

Design:
- No rest calibration applied: raw values are converted only.
- ponytail: the lidar passes through as a channel of the same stream
  (lidar_raw, lidar_distance_mm). Ceiling: one stream carries inertial sensors
  and a distance. Upgrade: a separate lidar port; the shared board/serial link
  stays an infrastructure detail of this module.
"""

import logging
from typing import Optional, Sequence

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorStreamSample,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)
from infrastructure.hardware.lsm9ds1.driver_lsm9ds1_stream import LSM9DS1StreamDriver
from infrastructure.hardware.lsm9ds1.lsm9ds1_conversion import (
    ACCELEROMETER_FULL_SCALE_G,
    GYROSCOPE_FULL_SCALE_DPS,
    MAGNETOMETER_FULL_SCALE_UT,
    lidar_raw_to_mm,
    raw_to_physical,
)
from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    ACCELEROMETER,
    GYROSCOPE,
    LIDAR,
    MAGNETOMETER,
)

logger = logging.getLogger(__name__)


class Lsm9ds1InertialSensorStreamAdapter(IInertialSensorStreamPort):
    def __init__(self, port: str, baudrate: int, rate_hz: Optional[int] = None) -> None:
        self._driver = LSM9DS1StreamDriver(port=port, baudrate=baudrate)
        self._port = port
        self._rate_hz = rate_hz
        self._connected = False

    def connect(self) -> None:
        logger.info("Lsm9ds1InertialSensorStreamAdapter: connect port=%s", self._port)
        self._driver.connect()
        self._connected = True

    def disconnect(self) -> None:
        logger.info("Lsm9ds1InertialSensorStreamAdapter: disconnect port=%s", self._port)
        self._driver.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def start_stream(self, channels: Sequence[str]) -> None:
        self._require_connected()
        logger.info(
            "Lsm9ds1InertialSensorStreamAdapter: start_stream channels=%s rate_hz=%s",
            list(channels),
            self._rate_hz,
        )
        self._driver.start_stream(channels, rate_hz=self._rate_hz)

    def stop_stream(self) -> None:
        self._driver.stop_stream()

    def read_sample(self, timeout_s: float = 1.0) -> Optional[InertialSensorStreamSample]:
        self._require_connected()
        got = self._driver.read_sample(timeout_s)
        if got is None:
            return None
        timestamp_s, raw = got
        fields = {}
        if ACCELEROMETER in raw:
            fields["acceleration_g"] = raw_to_physical(raw[ACCELEROMETER], ACCELEROMETER_FULL_SCALE_G)
        if GYROSCOPE in raw:
            fields["angular_rate_dps"] = raw_to_physical(raw[GYROSCOPE], GYROSCOPE_FULL_SCALE_DPS)
        if MAGNETOMETER in raw:
            fields["magnetic_field_ut"] = raw_to_physical(raw[MAGNETOMETER], MAGNETOMETER_FULL_SCALE_UT)
        if LIDAR in raw:
            fields["lidar_raw"] = raw[LIDAR][0]
            fields["lidar_distance_mm"] = lidar_raw_to_mm(raw[LIDAR][0])
        return InertialSensorStreamSample(timestamp_s=timestamp_s, **fields)

    def _require_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("inertial sensor not connected")
