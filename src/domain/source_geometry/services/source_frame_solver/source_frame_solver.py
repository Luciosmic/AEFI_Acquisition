"""
Source Frame Solver - Domain Service

Responsibility:
- Reconstruct the 4 excitation sphere positions from the 6 measured
  pairwise distances (Distance Geometry Problem, exact analytic solution).
- Derive the canonical source frame (centroid, axes, rotation matrix).
- Pure business logic, no side effects, no I/O.

Rationale:
- Algorithm from config_templates/NOTE - Source Frame Geometry.md §3-4.
"""
import numpy as np

from domain.source_geometry.value_objects.source_geometry.source_geometry import SourceGeometry
from domain.source_geometry.value_objects.source_frame_geometry.source_frame_geometry import (
    SourceFrameGeometry,
)


class SourceFrameSolver:
    """Solves the 4-sphere DGP and derives the canonical source frame."""

    @staticmethod
    def solve(
        geometry: SourceGeometry,
        degeneracy_tolerance: float = 1e-4,
        coplanarity_tolerance: float = 1e-4,
        orthogonality_tolerance: float = 1e-3,
    ) -> SourceFrameGeometry:
        # ponytail: degeneracy_tolerance (m^2) is slack on the squared-distance discriminants
        # below. A real bench measured with a 0.02mm-resolution caliper is not perfectly
        # coplanar/symmetric, and the DGP equations amplify that raw noise well beyond
        # 0.02mm once squared and combined across 6 measurements (observed ~3mm-equivalent
        # on the real device, see source_frame_solver_test.py::test_real_device_measurement).
        # 1e-4 accepts that amplified noise while still catching truly inconsistent inputs
        # (e.g. a swapped distance), which miss by orders of magnitude more. coplanarity_tolerance
        # (m, linear) is the separate, tighter threshold for the is_coplanar flag itself.
        # Tighten degeneracy_tolerance once a proper GUM propagation through the DGP exists.
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
        p3 = np.array([x3, np.sqrt(max(y3_sq, 0.0)), 0.0])
        y3 = p3[1]

        x4 = (d12**2 + d14**2 - d24**2) / (2 * d12)
        y4 = (d13**2 + d14**2 - d34**2 - 2 * x3 * x4) / (2 * y3)
        z4_sq = d14**2 - x4**2 - y4**2
        if z4_sq < -degeneracy_tolerance:
            raise ValueError(
                f"Degenerate configuration for S4: d14^2 ({d14**2:.3e}) < x4^2+y4^2 "
                f"({x4**2 + y4**2:.3e})"
            )
        z4 = np.sqrt(max(z4_sq, 0.0))
        p4 = np.array([x4, y4, z4])

        positions = (p1, p2, p3, p4)
        centroid = np.mean(positions, axis=0)

        x_axis = _normalize(p1 - p2)
        y_axis = _normalize(p3 - p4)
        z_axis = np.cross(x_axis, y_axis)

        is_coplanar = bool(abs(z4) < coplanarity_tolerance)
        is_orthogonal = bool(abs(np.dot(x_axis, y_axis)) < orthogonality_tolerance)

        rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])

        return SourceFrameGeometry(
            positions=tuple(tuple(p) for p in positions),
            centroid=tuple(centroid),
            x_axis=tuple(x_axis),
            y_axis=tuple(y_axis),
            z_axis=tuple(z_axis),
            rotation_matrix=tuple(tuple(row) for row in rotation_matrix),
            is_coplanar=is_coplanar,
            is_orthogonal=is_orthogonal,
        )


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return vector / norm
