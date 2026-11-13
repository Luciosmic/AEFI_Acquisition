"""Caractérisation de motion_failed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motion_failed.motion_failed import MotionFailed


def test_motionfailed_garde_ses_champs() -> None:
    motion_id = "x"
    error = "x"
    instance = MotionFailed(motion_id=motion_id, error=error)
    assert isinstance(instance, DomainEvent)
    assert instance.motion_id == motion_id
    assert instance.error == error


def test_motionfailed_est_immuable() -> None:
    motion_id = "x"
    error = "x"
    instance = MotionFailed(motion_id=motion_id, error=error)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.motion_id = motion_id  # type: ignore[misc]
