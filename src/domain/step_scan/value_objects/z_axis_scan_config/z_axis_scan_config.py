"""
Domain: Z Axis Scan Config

Responsibility:
    Describe a Z-only scan at a fixed XY position.

Design:
    Says nothing about how Z is driven (manual operator vs motor):
    that is an execution concern, not domain data.
"""
from dataclasses import dataclass

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.physical_bench_limits import (
    PHYSICAL_X_MAX_MM,
    PHYSICAL_Y_MAX_MM,
    PHYSICAL_Z_MAX_MM,
)


@dataclass(frozen=True)
class ZAxisScanConfig:
    """Z-only scan. Units: mm."""

    xy_position: Position2D
    z_min_mm: float
    z_max_mm: float
    n_points: int

    def __post_init__(self):
        p = self.xy_position
        if not (0 <= p.x <= PHYSICAL_X_MAX_MM and 0 <= p.y <= PHYSICAL_Y_MAX_MM):
            raise ValueError(
                f"XY position ({p.x}, {p.y}) outside bench limits "
                f"[0, {PHYSICAL_X_MAX_MM}] x [0, {PHYSICAL_Y_MAX_MM}]"
            )
        if not (0 <= self.z_min_mm < self.z_max_mm <= PHYSICAL_Z_MAX_MM):
            raise ValueError(
                f"Invalid Z range: [{self.z_min_mm}, {self.z_max_mm}]. "
                f"Must be 0 <= z_min < z_max <= {PHYSICAL_Z_MAX_MM}"
            )
        if self.n_points < 1:
            raise ValueError(f"n_points must be >= 1, got {self.n_points}")
