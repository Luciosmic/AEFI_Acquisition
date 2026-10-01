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
- The 4 spheres are coplanar by construction of the source — a known
  constraint, not a hypothesis to test — so every center is solved in z=0.
  Treating S4's height as a free unknown produced a negative discriminant on
  real data: an ill-posed problem, not a sign of non-planarity.
- 6 measured distances for 5 degrees of freedom (4 planar centers minus a
  rigid motion): one redundant measurement. Linear least squares over
  linearized rows is wrong (collinear rows, residual two orders of magnitude
  worse); nonlinear least squares on the original distance equations is
  required.
- Fitting only S4 (S1, S2, S3 exact) dumped the whole inconsistency on S4's
  3 distances: a symmetric input (all sides 85mm, both diagonals 110mm)
  came out as a lopsided quadrilateral (2026-10-01). All 4 centers are now
  refined together over the 6 distances, so a symmetric input gives a
  symmetric result.

Design:
- Work frame (S1 at origin, S2 on +x) is an internal computational
  convenience, never exposed. Positions are returned in the source frame:
  centroid origin, +x/+y along the sides of the best-fit square (the source
  is ideally an axis-aligned square), each sphere in its labeled quadrant.
  Built in two rigid steps — side midpoints give the quadrant orientation
  (resolves the mirror ambiguity distances alone leave), then a rotation
  aligns the best-fit square — so distances and residuals are unchanged.
  Aligning on the side midpoints alone favored the S1-S3/S4-S2 sides: on
  real measurements the best-fit square came out tilted by half the
  arrangement's shear (0.7°, 2026-10-01).
- Best-fit square by 4-point DFT over the perimeter S1→S3→S2→S4 (S1<->S2 and
  S3<->S4 are the diagonals). That order winds clockwise in the source
  frame, so the square generator is w=-i; the CCW convention silently picks
  the near-zero harmonic (~1mm "side" on real data instead of ~64mm).
- Impossible measurements raise SourceGeometryInconsistentError.
"""

import cmath
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
# S1 corner (x_neg_y_pos) of an axis-aligned square seen from its center
_ALIGNED_S1_PHASE = 3 * math.pi / 4


class SourceFrameSolver:
    @staticmethod
    def solve(entry: SourceGeometryCalibrationEntry) -> SourceFrameGeometry:
        d = entry.center_to_center_distances_m
        positions = _align_on_fitted_square(_to_source_frame(_solve_work_frame(d)))
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
    # S4 seed: exact against S1 and S2, d34 picks its side of the S1-S2 axis
    x4 = (d12**2 + d[(S1, S4)] ** 2 - d[(S2, S4)] ** 2) / (2 * d12)
    y4 = (x3**2 + y3**2 + d[(S1, S4)] ** 2 - d[(S3, S4)] ** 2 - 2 * x3 * x4) / (2 * y3)
    seed = np.array((0.0, 0.0, d12, 0.0, x3, y3, x4, y4))

    def residuals(flat):
        p = flat.reshape(4, 2)
        return [np.linalg.norm(p[i] - p[j]) - d_ij for (i, j), d_ij in d.items()]

    # all 4 centers refined together: the measurement inconsistency is spread
    # over the 6 distances instead of being dumped on whichever sphere is
    # solved last. Rigid-motion gauge left free, removed by _to_source_frame.
    return list(least_squares(residuals, x0=seed).x.reshape(4, 2))


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


def _square_harmonic(positions):
    """(center, z0) of the least-squares perfect square through the 4 centers:
    corner k of the clockwise perimeter S1→S3→S2→S4 is center + z0·i^(-k)."""
    z = [complex(*positions[i]) for i in PERIMETER_ORDER]
    center = sum(z) / 4
    return center, sum((zk - center) * 1j**k for k, zk in enumerate(z)) / 4


def _align_on_fitted_square(positions):
    """Rotate about the centroid (already the origin) so the best-fit square's
    sides lie along x and y — the source is ideally an axis-aligned square;
    the arrangement's deviation is then shared symmetrically between sides."""
    _, z0 = _square_harmonic(positions)
    turn = cmath.exp(-1j * (cmath.phase(z0) - _ALIGNED_S1_PHASE))
    return [np.array(((complex(*p) * turn).real, (complex(*p) * turn).imag)) for p in positions]


def _fit_square(positions):
    """Least-squares perfect square through the 4 centers. Returns (ideal
    corner per sphere S1..S4, side length)."""
    center, z0 = _square_harmonic(positions)
    ideal = [0j] * 4
    for k, sphere in enumerate(PERIMETER_ORDER):
        corner = center + z0 * 1j ** (-k)
        ideal[sphere] = (corner.real, corner.imag)
    return tuple(ideal), abs(z0) * math.sqrt(2)
