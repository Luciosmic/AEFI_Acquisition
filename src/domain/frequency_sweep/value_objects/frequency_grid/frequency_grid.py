"""FrequencyGrid value object (see frequency_grid_intention.md)."""

import math
from dataclasses import dataclass
from typing import Tuple

MIN_FREQUENCIES = 2
# Frequencies are kept to the millihertz: two grids built from the same
# bounds compare equal, and the exported values stay readable.
_DECIMALS = 3


@dataclass(frozen=True)
class FrequencyGrid:
    """Excitation frequencies of a sweep, in Hz, strictly ascending."""

    frequencies_hz: Tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.frequencies_hz) < MIN_FREQUENCIES:
            raise ValueError(f"a frequency grid needs at least {MIN_FREQUENCIES} frequencies")
        if any(not math.isfinite(f) or f <= 0 for f in self.frequencies_hz):
            raise ValueError("every frequency must be a finite positive number of Hz")
        if any(later <= earlier for earlier, later in zip(self.frequencies_hz, self.frequencies_hz[1:])):
            raise ValueError("frequencies must be strictly ascending (no duplicate)")

    @classmethod
    def logarithmic(cls, start_hz: float, stop_hz: float, count: int) -> "FrequencyGrid":
        """`count` frequencies from `start_hz` to `stop_hz` included, evenly
        spaced on a logarithmic scale."""
        if count < MIN_FREQUENCIES:
            raise ValueError(f"a frequency grid needs at least {MIN_FREQUENCIES} frequencies")
        if not (start_hz > 0 and stop_hz > start_hz):
            raise ValueError("a logarithmic grid needs 0 < start < stop")
        ratio = (stop_hz / start_hz) ** (1.0 / (count - 1))
        return cls(tuple(round(start_hz * ratio ** i, _DECIMALS) for i in range(count - 1)) + (round(stop_hz, _DECIMALS),))

    def __len__(self) -> int:
        return len(self.frequencies_hz)

    def index_of(self, frequency_hz: float) -> int:
        """Position of `frequency_hz` in the grid; ValueError if absent."""
        return self.frequencies_hz.index(frequency_hz)
