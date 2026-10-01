"""
Source Frame Solver

Responsibility:
- Reconstruct the 4 excitation sphere centers from a caliper-measured
  SourceGeometryCalibrationEntry (coplanar Distance Geometry Problem), express
  them in the source frame, and fit the best perfect square through them.
- Pure business computation, no I/O.

Rationale:
- Algorithm from "NOTE - Source Frame Geometry" (Luis Saluden's vault, not
  tracked in this repo) §3-4, validated in external_modules/source_geometry/
  (2026-07-24 → 2026-07-29) before moving here.
- The 4 spheres are coplanar by construction of the bench — a known
  constraint, not a hypothesis to test — so every center is solved in z=0.
  Treating S4's height as a free unknown produced a negative discriminant on
  real data: an ill-posed problem, not a sign of non-planarity.
- S1, S2, S3 are placed by exact elimination. S4 is over-determined (d14,
  d24, d34 for 2 unknowns): linear least squares over the 3 linearized rows
  is wrong (the 3rd row is a linear combination of the other two, residual
  two orders of magnitude worse); only nonlinear least squares on the 3
  original distance equations uses the redundant measurement correctly.

Design:
- Work frame (S1 at origin, S2 on +x) is an internal computational
  convenience, never exposed: positions are returned in the source frame
  (centroid origin, +x/+y through side midpoints, Gram-Schmidt
  orthogonalized) where each sphere lands in its labeled quadrant. Rigid
  transform, so distances and square residuals are unchanged.
- Best-fit square by 4-point DFT over the perimeter S1→S3→S2→S4 (S1<->S2 and
  S3<->S4 are the diagonals). That order winds clockwise in the source
  frame, so the square generator is w=-i; the CCW convention silently picks
  the near-zero harmonic (~1mm "side" on real data instead of ~64mm).
- Impossible measurements raise SourceGeometryInconsistentError.
"""

import math

import numpy as np
from scipy.optimize import least_squares

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.errors.source_geometry_inconsistent_error import SourceGeometryInconsistentError
from domain.calibration.value_objects.source_frame_geometry.source_frame_geometry import SourceFrameGeometry

S1, S2, S3, S4 = range(4)
PERIMETER_ORDER = (S1, S3, S2, S4)


class SourceFrameSolver:
    @staticmethod
    def solve(entry: SourceGeometryCalibrationEntry) -> SourceFrameGeometry:
        d = entry.center_to_center_distances_m
        positions = _to_source_frame(_solve_work_frame(d))
        ideal, side = _fit_square(positions)
        return SourceFrameGeometry(
            sphere_positions_m=tuple((float(x), float(y)) for x, y in positions),
            sphere_radii_m=tuple(m.value_m / 2 for m in entry.sphere_diameters),
            best_fit_square_positions_m=ideal,
            best_fit_square_side_m=side,
            distance_residuals_m=tuple(
                float(np.linalg.norm(positions[i] - positions[j])) - d_ij for (i, j), d_ij in d.items()
            ),
        )


def _solve_work_frame(d):
    d12, d13, d23 = d[(S1, S2)], d[(S1, S3)], d[(S2, S3)]
    x3 = (d12**2 + d13**2 - d23**2) / (2 * d12)
    y3_sq = d13**2 - x3**2
    if y3_sq <= 0:
        raise SourceGeometryInconsistentError(
            "Triangle S1-S2-S3 cannot close with the measured D_S1_S2, D_S1_S3, D_S2_S3"
        )
    y3 = math.sqrt(y3_sq)
    x4, y4 = _solve_s4(x3, y3, d12, d[(S1, S4)], d[(S2, S4)], d[(S3, S4)])
    return [np.array(p) for p in ((0.0, 0.0), (d12, 0.0), (x3, y3), (x4, y4))]


def _solve_s4(x3, y3, d12, d14, d24, d34):
    """Seeded by exact elimination against S1 and S2 (picking S4's side of the
    S1-S2 axis with d34), refined by nonlinear least squares on all 3
    distance equations."""
    x4_0 = (d12**2 + d14**2 - d24**2) / (2 * d12)
    y4_0 = (x3**2 + y3**2 + d14**2 - d34**2 - 2 * x3 * x4_0) / (2 * y3)

    def residuals(point):
        x4, y4 = point
        return [
            math.hypot(x4, y4) - d14,
            math.hypot(x4 - d12, y4) - d24,
            math.hypot(x4 - x3, y4 - y3) - d34,
        ]

    result = least_squares(residuals, x0=(x4_0, y4_0))
    return result.x[0], result.x[1]


def _to_source_frame(p):
    centroid = sum(p) / 4
    top_mid, bottom_mid = (p[S1] + p[S3]) / 2, (p[S2] + p[S4]) / 2
    left_mid, right_mid = (p[S1] + p[S4]) / 2, (p[S3] + p[S2]) / 2
    x_axis = _normalize(right_mid - left_mid)
    y_raw = top_mid - bottom_mid
    y_axis = _normalize(y_raw - np.dot(y_raw, x_axis) * x_axis)
    return [np.array((np.dot(pi - centroid, x_axis), np.dot(pi - centroid, y_axis))) for pi in p]


def _normalize(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise SourceGeometryInconsistentError("Spheres collapse onto a line: no source frame can be defined")
    return vector / norm


def _fit_square(positions):
    """Least-squares perfect square through the 4 centers. Returns (ideal
    corner per sphere S1..S4, side length)."""
    z = [complex(*positions[i]) for i in PERIMETER_ORDER]
    center = sum(z) / 4
    z0 = sum((zk - center) * 1j**k for k, zk in enumerate(z)) / 4
    ideal = [0j] * 4
    for k, sphere in enumerate(PERIMETER_ORDER):
        corner = center + z0 * 1j ** (-k)
        ideal[sphere] = (corner.real, corner.imag)
    return tuple(ideal), abs(z0) * math.sqrt(2)
