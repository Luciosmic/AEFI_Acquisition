"""Tests for SourceFrameSolver (DGP reconstruction)."""
import math

import pytest

from domain.source_geometry.value_objects.source_geometry.source_geometry import SourceGeometry
from domain.source_geometry.services.source_frame_solver.source_frame_solver import (
    SourceFrameSolver,
)

PAIRS = {
    "d_12": (0, 1), "d_13": (0, 2), "d_14": (0, 3),
    "d_23": (1, 2), "d_24": (1, 3), "d_34": (2, 3),
}


def distance(a, b):
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def assert_round_trip(geometry: SourceGeometry, result, tol=1e-9):
    """Reconstructed positions must reproduce every input distance."""
    for field, (i, j) in PAIRS.items():
        expected = getattr(geometry, field)
        actual = distance(result.positions[i], result.positions[j])
        assert actual == pytest.approx(expected, abs=tol), field


def test_ideal_symmetric_cross_is_coplanar_and_orthogonal():
    d_source = 0.1
    d_crossed = d_source / math.sqrt(2)
    geometry = SourceGeometry(
        d_12=d_source, d_34=d_source,
        d_13=d_crossed, d_14=d_crossed, d_23=d_crossed, d_24=d_crossed,
    )

    result = SourceFrameSolver.solve(geometry)

    assert_round_trip(geometry, result)
    assert result.is_coplanar
    assert result.is_orthogonal
    assert result.positions[0] == (0.0, 0.0, 0.0)
    assert result.positions[1] == pytest.approx((d_source, 0.0, 0.0))


def test_real_device_measurement_2026_07_24():
    """Values from mesures-dgp-pied-a-coulisse-4spheres.md, converted to
    center-to-center via config_templates/aefi_device_config.json."""
    geometry = SourceGeometry(
        d_12=0.09182, d_13=0.06481, d_14=0.06397,
        d_23=0.06275, d_24=0.06495, d_34=0.08958,
    )

    result = SourceFrameSolver.solve(geometry)

    # Real, noisy measurements: z4^2 comes out slightly negative and gets clamped to
    # 0 (near-coplanar bench), so round-trip distances involving S4 only match up to
    # the amplified measurement noise (~0.1mm here), not machine precision.
    assert_round_trip(geometry, result, tol=1e-4)
    assert result.is_coplanar


def test_degenerate_triangle_raises():
    geometry = SourceGeometry(d_12=0.1, d_13=0.01, d_14=0.07, d_23=0.01, d_24=0.07, d_34=0.1)

    with pytest.raises(ValueError, match="Degenerate triangle"):
        SourceFrameSolver.solve(geometry)


def test_rotation_matrix_columns_are_the_axes():
    d_source = 0.1
    d_crossed = d_source / math.sqrt(2)
    geometry = SourceGeometry(
        d_12=d_source, d_34=d_source,
        d_13=d_crossed, d_14=d_crossed, d_23=d_crossed, d_24=d_crossed,
    )

    result = SourceFrameSolver.solve(geometry)

    columns = list(zip(*result.rotation_matrix))
    assert columns[0] == pytest.approx(result.x_axis)
    assert columns[1] == pytest.approx(result.y_axis)
    assert columns[2] == pytest.approx(result.z_axis)
