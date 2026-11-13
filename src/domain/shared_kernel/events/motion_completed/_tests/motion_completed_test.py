"""Caractérisation de motion_completed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motion_completed.motion_completed import MotionCompleted
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def test_motioncompleted_garde_ses_champs() -> None:
    motion_id = "x"
    final_position = Position2D(x=1.5, y=1.5)
    duration_ms = 1.5
    instance = MotionCompleted(motion_id=motion_id, final_position=final_position, duration_ms=duration_ms)
    assert isinstance(instance, DomainEvent)
    assert instance.motion_id == motion_id
    assert instance.final_position == final_position
    assert instance.duration_ms == duration_ms


def test_motioncompleted_est_immuable() -> None:
    motion_id = "x"
    final_position = Position2D(x=1.5, y=1.5)
    duration_ms = 1.5
    instance = MotionCompleted(motion_id=motion_id, final_position=final_position, duration_ms=duration_ms)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.motion_id = motion_id
