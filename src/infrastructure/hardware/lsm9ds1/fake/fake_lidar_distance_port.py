"""
Fake LIDAR Distance Port

See fake_lidar_distance_port_intention.md.
"""

import random
from typing import Callable, Optional

from application.services.lidar_distance.dtos.lidar_distance_dtos import (
    LidarDistanceReading,
)
from application.services.lidar_distance.ports.i_lidar_distance_port import (
    ILidarDistancePort,
)
from application.services.lidar_distance.ports.lidar_stream_error import (
    LidarStreamBusyError,
    LidarUnavailableError,
)
from domain.detection_devices.lidar.lidar_distance.lidar_distance import LidarDistance
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import LIDAR_CAP_HZ

# Measured on the real board (journal 2026-10-12): 25 Hz as soon as the LIDAR is active.
SAMPLE_PERIOD_S = 1.0 / LIDAR_CAP_HZ


class FakeLidarDistancePort(ILidarDistancePort):
    """A reading every SAMPLE_PERIOD_S of the injected clock, from `distance_mm()`."""

    def __init__(
        self,
        distance_mm: Callable[[], Optional[float]],
        clock,
        streamed_elsewhere: bool = False,
        fail_on_open: bool = False,
        silent_after_samples: Optional[int] = None,
        no_return_ratio: float = 0.0,
        seed: int = 0,
    ) -> None:
        """`clock`: now()/sleep() (FakeClock). `distance_mm()` is called at each
        sample, e.g. a bar scene reading a fake motion port; None means no return
        (a floor out of range). `no_return_ratio`: share of the valid distances
        turned into sporadic "no return" dropouts, like the real LIDAR's 0."""
        if not 0.0 <= no_return_ratio < 1.0:
            raise ValueError(f"no_return_ratio must be in [0, 1), got {no_return_ratio}")
        self._distance_mm = distance_mm
        self._no_return_ratio = no_return_ratio
        self._rng = random.Random(seed)
        self.no_return_sent = 0
        self._clock = clock
        self.streamed_elsewhere = streamed_elsewhere
        self._fail_on_open = fail_on_open
        self._silent_after = silent_after_samples
        self._open = False
        self._next_sample_at = 0.0
        self.samples_sent = 0
        self.open_count = 0
        self.close_count = 0

    def is_streamed_elsewhere(self) -> bool:
        return self.streamed_elsewhere

    def open(self) -> None:
        if self.streamed_elsewhere:
            raise LidarStreamBusyError("le panneau du capteur inertiel diffuse déjà le flux")
        if self._fail_on_open:
            raise LidarUnavailableError("échec simulé à l'ouverture du flux LIDAR")
        self._open = True
        self.open_count += 1
        self._next_sample_at = self._clock.now() + SAMPLE_PERIOD_S

    @property
    def is_open(self) -> bool:
        return self._open

    def read_distance(self, timeout_s: float) -> Optional[LidarDistanceReading]:
        if not self._open:
            raise LidarUnavailableError("flux LIDAR non ouvert")
        silent = self._silent_after is not None and self.samples_sent >= self._silent_after
        now = self._clock.now()
        if silent or self._next_sample_at > now + timeout_s:
            self._clock.sleep(timeout_s)
            return None
        # Reception order, like the real adapter's queue: readings that arrived
        # while nobody read come out at once, with their arrival time.
        if self._next_sample_at > now:
            self._clock.sleep(self._next_sample_at - now)
        timestamp = self._next_sample_at
        self._next_sample_at += SAMPLE_PERIOD_S
        self.samples_sent += 1
        # ponytail: the distance is evaluated now, not at `timestamp` — exact for
        # the readings taken at once (fly scan) and at rest; a buffered reading
        # from during a move carries the position at reading time (the service
        # discards those: they precede the settling).
        distance_mm = self._distance_mm()
        if distance_mm is not None and self._no_return_ratio and self._rng.random() < self._no_return_ratio:
            distance_mm = None
        if distance_mm is None:
            self.no_return_sent += 1
            return LidarDistanceReading(timestamp_s=timestamp, distance=LidarDistance.no_return())
        return LidarDistanceReading(timestamp_s=timestamp, distance=LidarDistance(distance_mm))

    def close(self) -> None:
        if self._open:
            self.close_count += 1
        self._open = False
