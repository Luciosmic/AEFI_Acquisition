"""Tests for SourceFrameSolver (coplanar DGP reconstruction)."""
import math

import pytest

from source_geometry.source_geometry import SourceGeometry
from source_geometry.source_frame_solver import SourceFrameSolver

PAIRS = {
    "d_12": (0, 1), "d_13": (0, 2), "d_14": (0, 3),
    "d_23": (1, 2), "d_24": (1, 3), "d_34": (2, 3),
}


def distance(a, b):
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def assert_round_trip(geometry: SourceGeometry, result, tol=1e-9):
    """Reconstructed positions must reproduce every derived input distance."""
    for field, (i, j) in PAIRS.items():
        expected = getattr(geometry, field)
        actual = distance(result.positions[i], result.positions[j])
        assert actual == pytest.approx(expected, abs=tol), field


def make_symmetric_geometry(d_source=0.1, r=0.01):
    d_crossed = d_source / math.sqrt(2)
    return SourceGeometry(
        D_12=d_source + 2 * r, D_34=d_source + 2 * r,
        D_13=d_crossed + 2 * r, D_14=d_crossed + 2 * r,
        D_23=d_crossed + 2 * r, D_24=d_crossed + 2 * r,
        phi_1=2 * r, phi_2=2 * r, phi_3=2 * r, phi_4=2 * r,
    )


def test_ideal_symmetric_cross_is_planar_and_orthogonal():
    geometry = make_symmetric_geometry()

    result = SourceFrameSolver.solve(geometry)

    assert_round_trip(geometry, result, tol=1e-6)
    assert result.is_orthogonal
    assert result.positions[0] == (0.0, 0.0, 0.0)
    assert result.positions[1] == pytest.approx((geometry.d_12, 0.0, 0.0))
    for position in result.positions:
        assert position[2] == 0.0  # coplanar by construction, not by inference


def test_real_device_measurement_2026_07_24():
    """Raw caliper readings from mesures-dgp-pied-a-coulisse-4spheres.md,
    fed directly (no manual pre-conversion — SourceGeometry derives d_ij)."""
    geometry = SourceGeometry(
        D_12=0.11142, D_13=0.08436, D_14=0.08352,
        D_23=0.08230, D_24=0.08450, D_34=0.10908,
        phi_1=0.0196, phi_2=0.0196, phi_3=0.0195, phi_4=0.0195,
    )

    result = SourceFrameSolver.solve(geometry)

    # Real, noisy measurements over-determine S4 (3 distances, 2 unknowns);
    # nonlinear least-squares distributes the residual instead of inventing
    # a fictitious height, so round trip only holds up to that residual
    # (~2e-5 m here, not machine precision).
    assert_round_trip(geometry, result, tol=5e-5)
    for position in result.positions:
        assert position[2] == 0.0


def test_degenerate_triangle_raises():
    geometry = SourceGeometry(
        D_12=0.12, D_13=0.03, D_14=0.09, D_23=0.03, D_24=0.09, D_34=0.12,
        phi_1=0.02, phi_2=0.02, phi_3=0.02, phi_4=0.02,
    )

    with pytest.raises(ValueError, match="Degenerate triangle"):
        SourceFrameSolver.solve(geometry)


def test_rotation_matrix_columns_are_the_axes():
    geometry = make_symmetric_geometry()

    result = SourceFrameSolver.solve(geometry)

    columns = list(zip(*result.rotation_matrix))
    assert columns[0] == pytest.approx(result.x_axis)
    assert columns[1] == pytest.approx(result.y_axis)
    assert columns[2] == pytest.approx(result.z_axis)
