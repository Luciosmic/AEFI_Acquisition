"""Caractérisation de scan_trajectory : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.value_objects.scan_trajectory.scan_trajectory import ScanTrajectory


def test_scantrajectory_garde_ses_champs():
    points = [Position2D(x=1.5, y=1.5)]
    instance = ScanTrajectory(points=points)
    assert instance.points == points


def test_scantrajectory_est_immuable():
    points = [Position2D(x=1.5, y=1.5)]
    instance = ScanTrajectory(points=points)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.points = points
