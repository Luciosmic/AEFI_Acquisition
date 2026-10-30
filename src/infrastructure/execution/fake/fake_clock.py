"""
Fake Clock

See fake_clock_intention.md.
"""

import threading


class FakeClock:
    """Virtual time: `now()` only moves when someone `sleep()`s."""

    def __init__(self, start_s: float = 0.0) -> None:
        self._now = start_s
        self._lock = threading.Lock()

    def now(self) -> float:
        with self._lock:
            return self._now

    def sleep(self, duration_s: float) -> None:
        if duration_s < 0:
            raise ValueError(f"duration_s must be >= 0, got {duration_s}")
        with self._lock:
            self._now += duration_s
