"""FrequencyGrid value object (see frequency_grid_intention.md)."""

import math
from dataclasses import dataclass
from typing import Iterable, Tuple

MIN_FREQUENCIES = 2
# Frequencies are kept to the millihertz: two grids built from the same
# bounds compare equal, and the exported values stay readable.
_DECIMALS = 3
# A bound that is a grid frequency (100 Hz at 10 per decade) stays in the grid
# despite the rounding of log10.
_ANCHOR_TOLERANCE = 1e-9


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
    def per_decade(cls, start_hz: float, stop_hz: float, points_per_decade: int) -> "FrequencyGrid":
        """The frequencies 10^(k/n) Hz (k integer, n = `points_per_decade`)
        between `start_hz` and `stop_hz` included. Anchored on the decades,
        not on the bounds: two grids with the same n share every frequency
        they have in common, whatever their bounds."""
        if points_per_decade < 1:
            raise ValueError("at least 1 point per decade")
        if not (math.isfinite(start_hz) and math.isfinite(stop_hz) and 0 < start_hz < stop_hz):
            raise ValueError("a logarithmic grid needs 0 < start < stop")
        n = points_per_decade
        first = math.ceil(n * math.log10(start_hz) - _ANCHOR_TOLERANCE)
        last = math.floor(n * math.log10(stop_hz) + _ANCHOR_TOLERANCE)
        return cls(tuple(round(10.0 ** (k / n), _DECIMALS) for k in range(first, last + 1)))

    @classmethod
    def from_list(cls, frequencies_hz: Iterable[float]) -> "FrequencyGrid":
        """The frequencies given by the operator, swept in ascending order
        (a duplicate is refused, not merged)."""
        return cls(tuple(sorted(round(f, _DECIMALS) for f in frequencies_hz)))

    def __len__(self) -> int:
        return len(self.frequencies_hz)

    def index_of(self, frequency_hz: float) -> int:
        """Position of `frequency_hz` in the grid; ValueError if absent."""
        return self.frequencies_hz.index(frequency_hz)
