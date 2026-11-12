"""ColumnRestCriterion value object (see column_rest_criterion_intention.md)."""

import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

Acceleration = Tuple[float, float, float]


@dataclass(frozen=True)
class ColumnRestCriterion:
    """When the column is back at rest after a move, judged on its accelerometer.

    Units: durations in s, accelerations in [g] (UCUM).
    Defaults come from the Banc-test-II campaigns (run of 2026-10-30 20:19: after a
    move the column rises to ~100 mg and takes 1 to 2 s to come back to ~7 mg).
    """

    # Rest level measured on the still column before the first move.
    rest_measurement_s: float = 10.0
    # Sliding window, ending now, on which the vibration is compared to the rest level.
    window_s: float = 1.0
    # At rest when the window vibration is at most factor × the rest level.
    factor: float = 1.5
    # Past this delay after the stop, the measurement starts anyway.
    timeout_s: float = 30.0

    def __post_init__(self):
        for name in ("rest_measurement_s", "window_s", "timeout_s"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be > 0, got {getattr(self, name)}")
        if self.factor < 1.0:
            raise ValueError(f"factor must be >= 1, got {self.factor}")

    def threshold_g(self, rest_vibration_g: float) -> float:
        return self.factor * rest_vibration_g

    def is_at_rest(self, window_vibration_g: float, rest_vibration_g: float) -> bool:
        return window_vibration_g <= self.threshold_g(rest_vibration_g)

    @staticmethod
    def vibration_g(accelerations: Sequence[Acceleration]) -> Optional[float]:
        """RMS of |a − ā| over the samples: sqrt(σx² + σy² + σz²), population σ.

        Independent of the board orientation; removes gravity and the board's
        static offset. None under two samples (nothing to judge on).
        """
        n = len(accelerations)
        if n < 2:
            return None
        mean = [sum(a[i] for a in accelerations) / n for i in range(3)]
        return math.sqrt(sum(sum((a[i] - mean[i]) ** 2 for i in range(3)) for a in accelerations) / n)
