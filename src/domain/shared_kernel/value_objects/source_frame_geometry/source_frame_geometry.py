"""
Domain: Source Frame Geometry

Responsibility:
    Immutable result of the DGP reconstruction: the cartesian positions of
    the 4 excitation spheres and the canonical source frame they define
    (centroid, axes, rotation matrix).

Rationale:
    See "NOTE - Source Frame Geometry" (Luis Saluden's vault, not tracked in
    this repo) sections 3-4. The 4 spheres are coplanar by construction of
    the bench (a known constraint, not something to verify after the fact),
    so all positions carry z=0 — there is no is_coplanar flag to report.

Design:
    - Frozen dataclass, pure data, no computation.
    - Built exclusively by SourceFrameSolver.solve().
    - Plain float tuples (not numpy arrays) to stay genuinely immutable.
"""
from dataclasses import dataclass
from typing import Tuple

Point3D = Tuple[float, float, float]


@dataclass(frozen=True)
class SourceFrameGeometry:
    """Reconstructed positions (S1..S4) and the source frame they define.

    Positions are expressed in the solver's anchoring frame (S1 at the
    origin, S2 on the x axis) — not yet in the canonical centroid-centered
    frame, which is `centroid` + `rotation_matrix` applied on top. All
    positions have z=0 (the 4 spheres are coplanar by construction).
    """

    positions: Tuple[Point3D, Point3D, Point3D, Point3D]  # P1, P2, P3, P4
    centroid: Point3D
    x_axis: Point3D
    y_axis: Point3D
    z_axis: Point3D
    rotation_matrix: Tuple[Point3D, Point3D, Point3D]  # rows; columns = axes
    is_orthogonal: bool
