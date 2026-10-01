"""Tests for ZAxisScanTrajectoryFactory."""
import pytest
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.value_objects.z_axis_scan_config.z_axis_scan_config import ZAxisScanConfig
from domain.step_scan.services.z_axis_scan_trajectory_factory.z_axis_scan_trajectory_factory import (
    ZAxisScanTrajectoryFactory,
)

XY = Position2D(600.0, 600.0)


def trajectory(n_points, z_min=10.0, z_max=50.0):
    config = ZAxisScanConfig(xy_position=XY, z_min_mm=z_min, z_max_mm=z_max, n_points=n_points)
    return ZAxisScanTrajectoryFactory.create_trajectory(config)


def test_equally_spaced_ascending():
    traj = trajectory(5)
    assert list(traj) == pytest.approx([10.0, 20.0, 30.0, 40.0, 50.0])
    assert traj.xy_position == XY


def test_single_point_is_z_min():
    assert list(trajectory(1)) == [10.0]


def test_two_points_are_range_bounds():
    assert list(trajectory(2)) == pytest.approx([10.0, 50.0])
