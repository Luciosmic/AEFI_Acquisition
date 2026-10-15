"""
Bar Point Reading Value Object

See bar_point_reading_intention.md.
"""

import math
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from domain.shared_kernel.value_objects.lidar_distance.lidar_distance import LidarDistance


class BarPointClassification(Enum):
    """Verdict on one point read at rest."""

    ON_BAR = "sur la barre"
    OFF_BAR = "hors barre"
    UNDECIDABLE = "indécidable"


@dataclass(frozen=True)
class BarPointReading:
    """k LIDAR distances read at rest at one motor position, summarized."""

    mean_distance_mm: float
    std_distance_mm: float
    sample_count: int

    def __post_init__(self):
        if self.sample_count < 2:
            raise ValueError(f"a point needs at least 2 samples (for its spread), got {self.sample_count}")
        if not math.isfinite(self.mean_distance_mm):
            raise ValueError(f"mean_distance_mm must be finite, got {self.mean_distance_mm}")
        if not math.isfinite(self.std_distance_mm) or self.std_distance_mm < 0:
            raise ValueError(f"std_distance_mm must be finite and >= 0, got {self.std_distance_mm}")

    @staticmethod
    def from_samples(distances_mm: Sequence[float]) -> "BarPointReading":
        if len(distances_mm) < 2:
            raise ValueError(f"a point needs at least 2 samples (for its spread), got {len(distances_mm)}")
        return BarPointReading(
            mean_distance_mm=statistics.fmean(distances_mm),
            std_distance_mm=statistics.stdev(distances_mm),
            sample_count=len(distances_mm),
        )

    @staticmethod
    def from_lidar(samples: Sequence[LidarDistance]) -> "BarPointReading":
        """Summary of the valid returns only: a "no return" is never averaged."""
        return BarPointReading.from_samples([s.distance_mm for s in samples if s.has_return])

    @staticmethod
    def has_enough_returns(samples: Sequence[LidarDistance], required_samples: int) -> bool:
        """True once the point holds the k valid returns it is classified on."""
        return sum(1 for s in samples if s.has_return) >= max(required_samples, 2)

    @staticmethod
    def classify_lidar(
        samples: Sequence[LidarDistance],
        required_samples: int,
        threshold_mm: Optional[float],
        k_sigma: float,
    ) -> BarPointClassification:
        """Verdict on the LIDAR samples of a point read at rest, "no return" included.

        At least `required_samples` valid returns: the usual verdict on their
        mean (any valid return is the bar when there is no threshold, i.e. the
        floor gives no return). No valid return at all: off the bar (the floor
        is out of range). Some, but fewer than required: undecidable."""
        if not samples:
            raise ValueError("a point needs at least one LIDAR sample, valid or without return")
        if BarPointReading.has_enough_returns(samples, required_samples):
            if threshold_mm is None:
                return BarPointClassification.ON_BAR
            return BarPointReading.from_lidar(samples).classify(threshold_mm, k_sigma)
        if not any(s.has_return for s in samples):
            return BarPointClassification.OFF_BAR
        return BarPointClassification.UNDECIDABLE

    def undecidable_half_width_mm(self, k_sigma: float) -> float:
        """k_σ · σ / √k: how close to the threshold the mean may not be trusted."""
        return k_sigma * self.std_distance_mm / math.sqrt(self.sample_count)

    def classify(self, threshold_mm: float, k_sigma: float) -> BarPointClassification:
        if k_sigma < 0:
            raise ValueError(f"k_sigma must be >= 0, got {k_sigma}")
        gap = self.mean_distance_mm - threshold_mm
        if gap == 0 or abs(gap) < self.undecidable_half_width_mm(k_sigma):
            return BarPointClassification.UNDECIDABLE
        # The bar is closer to the LIDAR than the floor: a short distance is on the bar.
        return BarPointClassification.ON_BAR if gap < 0 else BarPointClassification.OFF_BAR
