"""Caractérisation de position_updated : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.position_updated.position_updated import PositionUpdated
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def test_positionupdated_garde_ses_champs() -> None:
    position = Position2D(x=1.5, y=1.5)
    is_moving = True
    instance = PositionUpdated(position=position, is_moving=is_moving)
    assert isinstance(instance, DomainEvent)
    assert instance.position == position
    assert instance.is_moving == is_moving


def test_positionupdated_est_immuable() -> None:
    position = Position2D(x=1.5, y=1.5)
    is_moving = True
    instance = PositionUpdated(position=position, is_moving=is_moving)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.position = position  # type: ignore[misc]
