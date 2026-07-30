"""Tests for fit_square (best-fit perfect square via 4-point DFT) and
to_physical_frame (quadrant-aligned display frame)."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from source_geometry.source_geometry import SourceGeometry
from source_geometry.source_frame_solver import SourceFrameSolver
from source_geometry.visualize_square_deviation import fit_square, to_physical_frame, PERIMETER_ORDER


def test_perfect_square_has_zero_residual():
    # side 10, centered at origin, corners in clockwise order (matches
    # PERIMETER_ORDER's actual winding in the solver frame)
    corners = [(-5, 5), (5, 5), (5, -5), (-5, -5)]

    center, side, angle, ideal, residual = fit_square(corners)

    assert center == pytest.approx((0, 0), abs=1e-9)
    assert side == pytest.approx(10, abs=1e-9)
    for rx, ry in residual:
        assert math.hypot(rx, ry) == pytest.approx(0, abs=1e-9)


def test_perturbed_square_has_matching_nonzero_residual():
    # same square, S2-equivalent corner (index 1) pushed 1mm outward
    corners = [(-5, 5), (6, 5), (5, -5), (-5, -5)]

    center, side, angle, ideal, residual = fit_square(corners)

    residual_norms = [math.hypot(rx, ry) for rx, ry in residual]
    assert max(residual_norms) > 0
    assert residual_norms.index(max(residual_norms)) == 1  # the perturbed corner
    # least-squares distributes some of the perturbation to the other 3 corners too
    assert sum(1 for n in residual_norms if n > 1e-9) > 1


def test_winding_direction_matches_solver_frame():
    """Regression check: S1,S3,S2,S4 winds *clockwise* in the solver's
    (x,y) frame. Getting this backwards silently picks the near-zero
    harmonic and produces a nonsense fit (checked once: ~1mm 'side' and
    ~45mm 'residuals' on real device data instead of ~64mm / ~1mm)."""
    # clockwise square, same shape as the real device's reconstructed
    # S1,S3,S2,S4 (left, top, right, bottom)
    corners = [(0, 0), (5, 5), (10, 0), (5, -5)]

    center, side, angle, ideal, residual = fit_square(corners)

    assert side == pytest.approx(math.dist(corners[0], corners[1]), abs=1e-6)  # 5*sqrt(2)
    for rx, ry in residual:
        assert math.hypot(rx, ry) == pytest.approx(0, abs=1e-9)


def test_physical_frame_places_each_sphere_in_its_own_quadrant():
    # real device measurement, 2026-07-24
    geometry = SourceGeometry(
        D_12=0.11142, D_13=0.08436, D_14=0.08352,
        D_23=0.08230, D_24=0.08450, D_34=0.10908,
        phi_1=0.0196, phi_2=0.0196, phi_3=0.0195, phi_4=0.0195,
    )
    result = SourceFrameSolver.solve(geometry)

    physical = to_physical_frame(result)  # S1..S4

    expected_signs = {0: (-1, +1), 1: (+1, -1), 2: (+1, +1), 3: (-1, -1)}  # S1..S4
    for i, (x, y) in enumerate(physical):
        sx, sy = expected_signs[i]
        assert x * sx > 0, f"S{i+1} expected x sign {sx}, got x={x}"
        assert y * sy > 0, f"S{i+1} expected y sign {sy}, got y={y}"


def test_physical_frame_is_a_rigid_transform_of_the_solver_frame():
    """to_physical_frame changes viewpoint only — fit_square's side length
    and residuals (frame-invariant, geometric quantities) must be identical
    whether computed in the solver's anchoring frame or the physical one."""
    geometry = SourceGeometry(
        D_12=0.11142, D_13=0.08436, D_14=0.08352,
        D_23=0.08230, D_24=0.08450, D_34=0.10908,
        phi_1=0.0196, phi_2=0.0196, phi_3=0.0195, phi_4=0.0195,
    )
    result = SourceFrameSolver.solve(geometry)

    solver_corners = [result.positions[i][:2] for i in PERIMETER_ORDER]
    _, solver_side, _, _, solver_residual = fit_square(solver_corners)

    physical = to_physical_frame(result)
    physical_corners = [physical[i] for i in PERIMETER_ORDER]
    _, physical_side, _, _, physical_residual = fit_square(physical_corners)

    assert physical_side == pytest.approx(solver_side, abs=1e-9)
    solver_norms = sorted(math.hypot(rx, ry) for rx, ry in solver_residual)
    physical_norms = sorted(math.hypot(rx, ry) for rx, ry in physical_residual)
    assert physical_norms == pytest.approx(solver_norms, abs=1e-9)
