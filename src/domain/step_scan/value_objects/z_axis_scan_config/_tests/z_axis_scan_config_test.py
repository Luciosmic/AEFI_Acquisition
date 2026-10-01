"""Tests for ZAxisScanConfig value object."""
import pytest
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.physical_bench_limits import PHYSICAL_X_MAX_MM, PHYSICAL_Z_MAX_MM
from domain.step_scan.value_objects.z_axis_scan_config.z_axis_scan_config import ZAxisScanConfig


def make(**overrides):
    params = dict(xy_position=Position2D(600.0, 600.0), z_min_mm=0.0, z_max_mm=100.0, n_points=11)
    params.update(overrides)
    return ZAxisScanConfig(**params)


def test_valid_config():
    assert make().n_points == 11


def test_full_z_range_is_accepted():
    make(z_min_mm=0.0, z_max_mm=PHYSICAL_Z_MAX_MM)


@pytest.mark.parametrize("z_min, z_max", [
    (-1.0, 100.0),                   # below 0
    (50.0, 50.0),                    # empty range
    (60.0, 50.0),                    # inverted
    (0.0, PHYSICAL_Z_MAX_MM + 1.0),  # above bench
])
def test_rejects_invalid_z_range(z_min, z_max):
    with pytest.raises(ValueError):
        make(z_min_mm=z_min, z_max_mm=z_max)


def test_rejects_xy_outside_bench():
    with pytest.raises(ValueError):
        make(xy_position=Position2D(PHYSICAL_X_MAX_MM + 1.0, 600.0))
    with pytest.raises(ValueError):
        make(xy_position=Position2D(600.0, -1.0))


@pytest.mark.parametrize("n_points", [0, -1])
def test_rejects_invalid_n_points(n_points):
    with pytest.raises(ValueError):
        make(n_points=n_points)
