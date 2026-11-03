"""Measured sample rate over a sliding window of reception timestamps (pure)."""

from collections import deque
from typing import Deque, Optional


class SampleRateMeter:
    def __init__(self, window_size: int = 50) -> None:
        self._timestamps: Deque[float] = deque(maxlen=max(2, window_size))

    def add(self, timestamp_s: float) -> None:
        self._timestamps.append(timestamp_s)

    def reset(self) -> None:
        self._timestamps.clear()

    @property
    def rate_hz(self) -> Optional[float]:
        if len(self._timestamps) < 2:
            return None
        span = self._timestamps[-1] - self._timestamps[0]
        if span <= 0:
            return None
        return (len(self._timestamps) - 1) / span
