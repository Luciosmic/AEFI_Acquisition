"""
Source Frame Geometry

Responsibility:
- Immutable result of the source geometry reconstruction: where the 4
  excitation sphere centers actually are in the source frame, and how far
  the bench deviates from a perfect square.

Design:
- Source frame: origin at the spheres' centroid, +x/+y through the side
  midpoints, so each sphere lands in the quadrant its label names
  (S1=x_neg_y_pos, S2=x_pos_y_neg, S3=x_pos_y_pos, S4=x_neg_y_neg) — the
  same frame as aefi_device_config.json's sphere_labels. z=0 for all 4
  (coplanar by construction of the bench), so positions are 2D.
- Every per-sphere tuple is ordered S1..S4; every per-distance tuple follows
  SourceGeometryCalibrationEntry.pairwise_distances_ext order.
- Built exclusively by SourceFrameSolver.solve().
"""

import math
from dataclasses import dataclass
from typing import Tuple

Point2D = Tuple[float, float]
SpherePoints = Tuple[Point2D, Point2D, Point2D, Point2D]  # S1..S4


@dataclass(frozen=True)
class SourceFrameGeometry:
    sphere_positions_m: SpherePoints
    sphere_radii_m: Tuple[float, float, float, float]
    best_fit_square_positions_m: SpherePoints  # ideal corner of each sphere
    best_fit_square_side_m: float
    # reconstructed - measured center-to-center distance; non-zero because the
    # 6 measured distances over-determine the 4 coplanar centers
    distance_residuals_m: Tuple[float, float, float, float, float, float]

    @property
    def square_residuals_m(self) -> SpherePoints:
        """Per-sphere (dx, dy) from its best-fit square corner — the bench's
        actual mechanical defect."""
        return tuple(
            (x - ix, y - iy)
            for (x, y), (ix, iy) in zip(self.sphere_positions_m, self.best_fit_square_positions_m)
        )

    @property
    def square_rms_residual_m(self) -> float:
        return math.sqrt(sum(dx**2 + dy**2 for dx, dy in self.square_residuals_m) / 4)
