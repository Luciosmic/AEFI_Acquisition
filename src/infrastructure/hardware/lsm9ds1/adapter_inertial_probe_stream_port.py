"""
LSM9DS1 inertial probe stream adapter

Responsibility:
- Implement IInertialProbeStreamPort over LSM9DS1StreamDriver and the
  LSB -> physical units conversion.

Design:
- No rest calibration applied: raw values are converted only.
- The lidar passes through as a channel of the same stream (see the ponytail
  note below).
"""

import logging
from typing import Optional, Sequence

from application.services.inertial_probe_service.dtos.inertial_probe_dtos import (
    InertialProbeStreamSample,
)
from application.services.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)
from domain.detection_devices.lidar.lidar_distance.lidar_distance import LidarDistance
from infrastructure.hardware.lsm9ds1.driver_lsm9ds1_stream import LSM9DS1StreamDriver
from infrastructure.hardware.lsm9ds1.lsm9ds1_conversion import (
    ACCELEROMETER_FULL_SCALE_G,
    GYROSCOPE_FULL_SCALE_DPS,
    LIDAR_MM_PER_LSB,
    MAGNETOMETER_FULL_SCALE_UT,
    raw_to_physical,
)
from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    ACCELEROMETER,
    GYROSCOPE,
    LIDAR,
    MAGNETOMETER,
)

logger = logging.getLogger(__name__)


# ponytail: the lidar passes through as a channel of the same stream (lidar_distance). Ceiling: one stream carries inertial sensors and a distance.
# Upgrade: a separate lidar port; the shared board/serial link stays an
# infrastructure detail of this module.
class Lsm9ds1InertialProbeStreamAdapter(IInertialProbeStreamPort):
    def __init__(self, port: str, baudrate: int, rate_hz: Optional[int] = None) -> None:
        self._driver = LSM9DS1StreamDriver(port=port, baudrate=baudrate)
        self._port = port
        self._rate_hz = rate_hz
        self._connected = False

    def connect(self) -> None:
        logger.info("Lsm9ds1InertialProbeStreamAdapter: connect port=%s", self._port)
        self._driver.connect()
        self._connected = True

    def disconnect(self) -> None:
        logger.info("Lsm9ds1InertialProbeStreamAdapter: disconnect port=%s", self._port)
        self._driver.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def start_stream(self, channels: Sequence[str]) -> None:
        self._require_connected()
        logger.info(
            "Lsm9ds1InertialProbeStreamAdapter: start_stream channels=%s rate_hz=%s",
            list(channels),
            self._rate_hz,
        )
        self._driver.start_stream(channels, rate_hz=self._rate_hz)

    def stop_stream(self) -> None:
        self._driver.stop_stream()

    def read_sample(self, timeout_s: float = 1.0) -> Optional[InertialProbeStreamSample]:
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
            fields["lidar_distance"] = LidarDistance.from_raw(raw[LIDAR][0], LIDAR_MM_PER_LSB)
        return InertialProbeStreamSample(timestamp_s=timestamp_s, **fields)

    def _require_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("inertial probe not connected")
