"""Caractérisation de motion_stopped : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motion_stopped.motion_stopped import MotionStopped


def test_motionstopped_garde_ses_champs() -> None:
    reason = "x"
    instance = MotionStopped(reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.reason == reason


def test_motionstopped_est_immuable() -> None:
    reason = "x"
    instance = MotionStopped(reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.reason = reason
