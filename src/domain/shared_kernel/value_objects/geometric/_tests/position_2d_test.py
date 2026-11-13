"""Caractérisation de geometric : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def test_position2d_garde_ses_champs() -> None:
    x = 1.5
    y = 1.5
    instance = Position2D(x=x, y=y)
    assert instance.x == x
    assert instance.y == y


def test_position2d_est_immuable() -> None:
    x = 1.5
    y = 1.5
    instance = Position2D(x=x, y=y)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.x = x
