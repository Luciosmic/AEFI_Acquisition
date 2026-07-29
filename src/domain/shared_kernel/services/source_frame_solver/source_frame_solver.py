"""
Source Frame Solver - Domain Service

Responsibility:
- Reconstruct the 4 excitation sphere positions from the 6 measured
  pairwise distances (Distance Geometry Problem, coplanar formulation).
- Derive the canonical source frame (centroid, axes, rotation matrix).
- Pure business logic, no side effects, no I/O.

Rationale:
- Algorithm from "NOTE - Source Frame Geometry" (Luis Saluden's vault, not
  tracked in this repo) §3-4. The 4 spheres are coplanar by construction of
  the bench — a known constraint, not a hypothesis to test — so all 4
  positions are solved for in the z=0 plane directly.
- S1, S2, S3 are placed by an exact 2-equation-per-point elimination (no
  redundant measurement). S4 is over-determined: 3 measured distances
  (d_14, d_24, d_34) constrain only 2 unknowns (x4, y4). Naively linearizing
  and using all 3 pairwise differences does NOT use the extra measurement
  correctly — the 3rd difference row is an exact linear combination of the
  other two (coefficient-collinear), so an ordinary linear least-squares fit
  over the 3 rows badly distorts the answer instead of averaging it (checked
  numerically: residual sum-of-squares two orders of magnitude worse than
  the true optimum). Only a proper nonlinear least-squares fit on the 3
  original distance equations correctly uses the redundant measurement.
"""
import math

import numpy as np
from scipy.optimize import least_squares

from domain.shared_kernel.value_objects.source_geometry.source_geometry import SourceGeometry
from domain.shared_kernel.value_objects.source_frame_geometry.source_frame_geometry import (
    SourceFrameGeometry,
)


class SourceFrameSolver:
    """Solves the coplanar 4-sphere DGP and derives the canonical source frame."""

    @staticmethod
    def solve(
        geometry: SourceGeometry,
        degeneracy_tolerance: float = 1e-4,
        orthogonality_tolerance: float = 1e-3,
    ) -> SourceFrameGeometry:
        d12, d13, d14 = geometry.d_12, geometry.d_13, geometry.d_14
        d23, d24, d34 = geometry.d_23, geometry.d_24, geometry.d_34

        p1 = np.array([0.0, 0.0, 0.0])
        p2 = np.array([d12, 0.0, 0.0])

        x3 = (d12**2 + d13**2 - d23**2) / (2 * d12)
        y3_sq = d13**2 - x3**2
        if y3_sq < -degeneracy_tolerance:
            raise ValueError(
                f"Degenerate triangle S1-S2-S3: d13^2 ({d13**2:.3e}) < x3^2 ({x3**2:.3e})"
            )
        y3 = math.sqrt(max(y3_sq, 0.0))
        p3 = np.array([x3, y3, 0.0])

        x4, y4 = _solve_p4(x3, y3, d12, d14, d24, d34)
        p4 = np.array([x4, y4, 0.0])

        positions = (p1, p2, p3, p4)
        centroid = np.mean(positions, axis=0)

        x_axis = _normalize(p1 - p2)
        y_axis = _normalize(p3 - p4)
        z_axis = np.cross(x_axis, y_axis)

        is_orthogonal = bool(abs(np.dot(x_axis, y_axis)) < orthogonality_tolerance)

        rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])

        return SourceFrameGeometry(
            positions=tuple(tuple(p) for p in positions),
            centroid=tuple(centroid),
            x_axis=tuple(x_axis),
            y_axis=tuple(y_axis),
            z_axis=tuple(z_axis),
            rotation_matrix=tuple(tuple(row) for row in rotation_matrix),
            is_orthogonal=is_orthogonal,
        )


def _solve_p4(x3, y3, d12, d14, d24, d34):
    """S4's (x4, y4): 3 measured distances (d14, d24, d34) for 2 unknowns.

    Seeded from the exact elimination using only (d14, d24, d34) against
    circles i (P1) and ii (P2) — already close to optimal in practice — then
    refined by nonlinear least-squares against all 3 original distance
    equations, which is the correct way to use the 3rd, redundant one.
    """
    x4_0 = (d12**2 + d14**2 - d24**2) / (2 * d12)
    y4_0 = (x3**2 + y3**2 + d14**2 - d34**2 - 2 * x3 * x4_0) / (2 * y3) if y3 != 0 else 0.0

    def residuals(point):
        x4, y4 = point
        return [
            math.hypot(x4, y4) - d14,
            math.hypot(x4 - d12, y4) - d24,
            math.hypot(x4 - x3, y4 - y3) - d34,
        ]

    result = least_squares(residuals, x0=(x4_0, y4_0))
    return result.x[0], result.x[1]


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return vector / norm
