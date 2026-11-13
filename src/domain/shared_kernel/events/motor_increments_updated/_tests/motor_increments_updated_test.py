"""Caractérisation de motor_increments_updated : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motor_increments_updated.motor_increments_updated import MotorIncrementsUpdated


def test_motorincrementsupdated_garde_ses_champs() -> None:
    x_increments = 3
    y_increments = 3
    is_moving = True
    instance = MotorIncrementsUpdated(x_increments=x_increments, y_increments=y_increments, is_moving=is_moving)
    assert isinstance(instance, DomainEvent)
    assert instance.x_increments == x_increments
    assert instance.y_increments == y_increments
    assert instance.is_moving == is_moving


def test_motorincrementsupdated_est_immuable() -> None:
    x_increments = 3
    y_increments = 3
    is_moving = True
    instance = MotorIncrementsUpdated(x_increments=x_increments, y_increments=y_increments, is_moving=is_moving)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.x_increments = x_increments
