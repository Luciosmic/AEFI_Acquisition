"""
Domain: Line Scan Config

Responsibility:
    Describe a 1D scan line in the XY plane, oriented by theta.

Design:
    x(s) = center.x + s*cos(theta), y(s) = center.y + s*sin(theta),
    s in [-length/2, +length/2]. Bounds validated on the endpoints,
    not via ScanZone (a vertical line has zero X extent).
"""
import math
from dataclasses import dataclass
from typing import Tuple

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.physical_bench_limits import PHYSICAL_X_MAX_MM, PHYSICAL_Y_MAX_MM

# Absorbs trig rounding (cos(90°) ~ 6e-17) so a line lying on a bench edge is accepted.
_BOUNDS_TOLERANCE_MM = 1e-9


@dataclass(frozen=True)
class LineScanConfig:
    """1D scan line. Units: mm, degrees."""

    center: Position2D
    length_mm: float
    n_points: int
    theta_deg: float

    # Per-point execution settings, read by the scan loop (same meaning as
    # in StepScanConfig).
    # ponytail: duplicated with StepScanConfig (fields + checks), extract a
    # shared per-point settings VO if a third scan type needs them.
    stabilization_delay_ms: int = 0
    averaging_per_position: int = 1
    differential_mode: bool = False
    # Unvalidated placeholder, same value/caveat as StepScanConfig.differential_settle_delay_ms.
    differential_settle_delay_ms: float = 50.0

    def __post_init__(self):
        if self.n_points < 1:
            raise ValueError(f"n_points must be >= 1, got {self.n_points}")
        if self.length_mm <= 0:
            raise ValueError(f"length_mm must be > 0, got {self.length_mm}")
        if self.stabilization_delay_ms < 0:
            raise ValueError(f"stabilization_delay_ms must be >= 0, got {self.stabilization_delay_ms}")
        if self.averaging_per_position < 1:
            raise ValueError(f"averaging_per_position must be >= 1, got {self.averaging_per_position}")
        if self.differential_settle_delay_ms < 0:
            raise ValueError(
                f"differential_settle_delay_ms must be >= 0, got {self.differential_settle_delay_ms}"
            )
        tol = _BOUNDS_TOLERANCE_MM
        for p in self.endpoints():
            if not (-tol <= p.x <= PHYSICAL_X_MAX_MM + tol and -tol <= p.y <= PHYSICAL_Y_MAX_MM + tol):
                raise ValueError(
                    f"Line endpoint ({p.x:.3f}, {p.y:.3f}) outside bench limits "
                    f"[0, {PHYSICAL_X_MAX_MM}] x [0, {PHYSICAL_Y_MAX_MM}]"
                )

    def point_at(self, s: float) -> Position2D:
        """Position at signed distance s (mm) from the center along the line."""
        theta = math.radians(self.theta_deg)
        return Position2D(
            x=self.center.x + s * math.cos(theta),
            y=self.center.y + s * math.sin(theta),
        )

    def total_points(self) -> int:
        return self.n_points

    def endpoints(self) -> Tuple[Position2D, Position2D]:
        half = self.length_mm / 2
        return self.point_at(-half), self.point_at(half)
