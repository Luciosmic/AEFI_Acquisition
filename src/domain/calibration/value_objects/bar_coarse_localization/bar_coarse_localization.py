"""
Bar Coarse Localization Value Object

See bar_coarse_localization_intention.md.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BarCoarseLocalization:
    """Plateaus, threshold and approximate fronts of the bar seen during the fly scan.

    `off_bar_distance_mm` is None when the floor gave no LIDAR return (out of
    range): the off-bar plateau is then "no return" and there is no threshold."""

    on_bar_distance_mm: float
    off_bar_distance_mm: Optional[float]
    plateau_noise_mm: float
    first_front_increment: float
    second_front_increment: float
    profile_point_count: int

    def __post_init__(self):
        if self.off_bar_distance_mm is not None and not self.on_bar_distance_mm < self.off_bar_distance_mm:
            raise ValueError(
                f"the bar must be closer than the floor: on_bar={self.on_bar_distance_mm} mm, "
                f"off_bar={self.off_bar_distance_mm} mm"
            )
        if not self.first_front_increment < self.second_front_increment:
            raise ValueError(
                f"first front ({self.first_front_increment}) must precede the second "
                f"({self.second_front_increment})"
            )
        if self.plateau_noise_mm < 0:
            raise ValueError(f"plateau_noise_mm must be >= 0, got {self.plateau_noise_mm}")

    @property
    def floor_returns(self) -> bool:
        """False when the floor is out of LIDAR range: off the bar means no return."""
        return self.off_bar_distance_mm is not None

    @property
    def threshold_mm(self) -> Optional[float]:
        """s = (d_haut + d_bas) / 2: where each front crosses; None without floor
        returns (any valid return is then the bar)."""
        if self.off_bar_distance_mm is None:
            return None
        return (self.on_bar_distance_mm + self.off_bar_distance_mm) / 2.0

    @property
    def contrast_mm(self) -> Optional[float]:
        if self.off_bar_distance_mm is None:
            return None
        return self.off_bar_distance_mm - self.on_bar_distance_mm

    @property
    def bar_length_increments(self) -> float:
        """Coarse N, before refinement."""
        return self.second_front_increment - self.first_front_increment
