"""
Fake inertial sensor stream adapter

Responsibility:
- Deterministic double of IInertialSensorStreamPort.
- ponytail: the simulated lidar is a channel of the same stream (see the port).
"""

import math
import time
from typing import Optional, Sequence, Tuple

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorStreamSample,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)
from infrastructure.hardware.lsm9ds1.lsm9ds1_conversion import lidar_raw_to_mm
from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    ACCELEROMETER,
    GYROSCOPE,
    LIDAR,
    MAGNETOMETER,
    normalize_sensors,
)

# Measured on the real board (journal 2026-10-12): the stream runs at 25 Hz as
# soon as the lidar is active, whatever the requested rate.
LIDAR_CAP_HZ = 25.0
NOMINAL_RATE_HZ = 25.0


class FakeInertialSensorStreamAdapter(IInertialSensorStreamPort):
    def __init__(
        self,
        rate_hz: float = NOMINAL_RATE_HZ,
        realtime: bool = True,
        simulate_connection_failure: bool = False,
        fail_after_samples: Optional[int] = None,
        stall_after_samples: Optional[int] = None,
    ) -> None:
        self._rate_hz = rate_hz
        self._realtime = realtime
        self._simulate_connection_failure = simulate_connection_failure
        self._fail_after_samples = fail_after_samples
        self._stall_after_samples = stall_after_samples
        self._connected = False
        self._channels: Optional[Tuple[str, ...]] = None
        self._k = 0
        self._period = 1.0 / rate_hz
        self._t0 = 0.0

    def connect(self) -> None:
        if self._simulate_connection_failure:
            raise TimeoutError("simulated inertial sensor timeout")
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False
        self._channels = None

    def is_connected(self) -> bool:
        return self._connected

    def start_stream(self, channels: Sequence[str]) -> None:
        if not self._connected:
            raise RuntimeError("inertial sensor not connected")
        self._channels = normalize_sensors(channels)
        rate = min(self._rate_hz, LIDAR_CAP_HZ) if LIDAR in self._channels else self._rate_hz
        self._period = 1.0 / rate
        self._k = 0
        self._t0 = time.perf_counter()

    def stop_stream(self) -> None:
        self._channels = None

    def read_sample(self, timeout_s: float = 1.0) -> Optional[InertialSensorStreamSample]:
        if not self._connected or self._channels is None:
            raise RuntimeError("stream not started")
        k = self._k
        if self._fail_after_samples is not None and k >= self._fail_after_samples:
            raise OSError("simulated serial read failure")
        if self._stall_after_samples is not None and k >= self._stall_after_samples:
            if self._realtime:
                time.sleep(min(timeout_s, 0.05))
            return None
        self._k += 1
        if self._realtime:
            wait = self._t0 + k * self._period - time.perf_counter()
            if wait > 0:
                time.sleep(wait)
            t = time.perf_counter()
        else:
            t = k * self._period
        fields = {}
        if ACCELEROMETER in self._channels:
            fields["acceleration_g"] = (0.0, 0.0, 1.0)
        if GYROSCOPE in self._channels:
            p = 0.1 * (k + 1)
            fields["angular_rate_dps"] = (math.sin(p), math.cos(p), 0.1 * math.sin(2 * p))
        if MAGNETOMETER in self._channels:
            p = 0.05 * k
            fields["magnetic_field_ut"] = (20.0 + 2.0 * math.sin(p), -5.0 + 2.0 * math.cos(p), 40.0)
        if LIDAR in self._channels:
            raw = 1250 + (k + 1) % 11
            fields["lidar_raw"] = raw
            fields["lidar_distance_mm"] = lidar_raw_to_mm(raw)
        return InertialSensorStreamSample(timestamp_s=t, **fields)
