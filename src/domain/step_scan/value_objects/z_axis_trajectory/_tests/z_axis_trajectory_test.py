"""Tests for ZAxisTrajectory value object."""
import pytest
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.value_objects.z_axis_trajectory.z_axis_trajectory import ZAxisTrajectory


def test_sequence_ergonomics():
    traj = ZAxisTrajectory(xy_position=Position2D(1.0, 2.0), z_values=[0.0, 10.0, 20.0])
    assert list(traj) == [0.0, 10.0, 20.0]
    assert len(traj) == 3
    assert traj.total_points == 3
    assert traj[1] == 10.0
    assert traj.xy_position == Position2D(1.0, 2.0)


def test_immutable():
    traj = ZAxisTrajectory(xy_position=Position2D(1.0, 2.0), z_values=[0.0])
    with pytest.raises(Exception):
        traj.xy_position = Position2D(0.0, 0.0)
