"""Tests for LineScanTrajectoryFactory."""
import math
import pytest
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.step_scan.services.line_scan_trajectory_factory.line_scan_trajectory_factory import (
    LineScanTrajectoryFactory,
)

CENTER = Position2D(600.0, 600.0)


def trajectory(theta_deg, n_points=5, length_mm=100.0):
    config = LineScanConfig(center=CENTER, length_mm=length_mm, n_points=n_points, theta_deg=theta_deg)
    return LineScanTrajectoryFactory.create_trajectory(config)


def coords(traj):
    return [(p.x, p.y) for p in traj]


def test_theta_0_is_pure_x():
    expected = [(550.0, 600.0), (575.0, 600.0), (600.0, 600.0), (625.0, 600.0), (650.0, 600.0)]
    assert coords(trajectory(0.0)) == pytest.approx(expected)


def test_theta_90_is_pure_y():
    expected = [(600.0, 550.0), (600.0, 575.0), (600.0, 600.0), (600.0, 625.0), (600.0, 650.0)]
    assert coords(trajectory(90.0)) == pytest.approx(expected)


def test_theta_minus_90_runs_y_backwards():
    expected = [(600.0, 650.0), (600.0, 625.0), (600.0, 600.0), (600.0, 575.0), (600.0, 550.0)]
    assert coords(trajectory(-90.0)) == pytest.approx(expected)


def test_theta_45_is_diagonal_with_requested_length():
    traj = trajectory(45.0)
    d = 50.0 / math.sqrt(2)
    assert coords(traj)[0] == pytest.approx((600.0 - d, 600.0 - d))
    assert coords(traj)[-1] == pytest.approx((600.0 + d, 600.0 + d))
    assert traj[0].distance_to(traj[-1]) == pytest.approx(100.0)


def test_single_point_is_line_start():
    traj = trajectory(0.0, n_points=1)
    assert traj.total_points == 1
    assert coords(traj) == pytest.approx([(550.0, 600.0)])


def test_point_count():
    assert len(trajectory(30.0, n_points=17)) == 17
