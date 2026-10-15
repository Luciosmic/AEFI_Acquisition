"""
Bar Point Reading Value Object

See bar_point_reading_intention.md.
"""

import math
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


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
