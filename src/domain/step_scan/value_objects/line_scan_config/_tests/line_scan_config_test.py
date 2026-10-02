"""Tests for LineScanConfig value object."""
import pytest
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.physical_bench_limits import PHYSICAL_X_MAX_MM
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig


def make(**overrides):
    params = dict(center=Position2D(600.0, 600.0), length_mm=100.0, n_points=11, theta_deg=0.0)
    params.update(overrides)
    return LineScanConfig(**params)


def test_valid_config():
    config = make()
    assert config.n_points == 11


def test_vertical_line_is_accepted():
    # Zero X extent must not be rejected (the ScanZone trap).
    make(theta_deg=90.0)


def test_vertical_line_on_bench_edge_is_accepted():
    # cos(90°) is ~6e-17, not 0: must not push x below 0.
    make(center=Position2D(0.0, 600.0), theta_deg=90.0)
    make(center=Position2D(0.0, 600.0), theta_deg=-90.0)


def test_endpoints():
    start, end = make(theta_deg=90.0).endpoints()
    assert start.x == pytest.approx(600.0)
    assert start.y == pytest.approx(550.0)
    assert end.y == pytest.approx(650.0)


@pytest.mark.parametrize("n_points", [0, -1])
def test_rejects_invalid_n_points(n_points):
    with pytest.raises(ValueError):
        make(n_points=n_points)


@pytest.mark.parametrize("length_mm", [0.0, -10.0])
def test_rejects_non_positive_length(length_mm):
    with pytest.raises(ValueError):
        make(length_mm=length_mm)


def test_rejects_line_leaving_bench_in_x():
    with pytest.raises(ValueError):
        make(center=Position2D(PHYSICAL_X_MAX_MM - 10.0, 600.0))


def test_rejects_rotated_line_leaving_bench_in_y():
    # Horizontal fits; same line rotated to vertical crosses y=0.
    make(center=Position2D(600.0, 10.0), length_mm=100.0)
    with pytest.raises(ValueError):
        make(center=Position2D(600.0, 10.0), length_mm=100.0, theta_deg=90.0)


def test_total_points():
    assert make(n_points=7).total_points() == 7


def test_execution_settings_defaults():
    config = make()
    assert config.stabilization_delay_ms == 0
    assert config.averaging_per_position == 1
    assert config.differential_mode is False


@pytest.mark.parametrize("overrides", [
    dict(stabilization_delay_ms=-1),
    dict(averaging_per_position=0),
    dict(differential_settle_delay_ms=-1.0),
])
def test_rejects_invalid_execution_settings(overrides):
    with pytest.raises(ValueError):
        make(**overrides)


def test_immutable():
    config = make()
    with pytest.raises(Exception):
        config.n_points = 3
