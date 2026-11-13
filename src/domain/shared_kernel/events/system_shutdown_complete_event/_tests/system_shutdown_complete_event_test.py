"""Caractérisation de system_shutdown_complete_event : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.system_shutdown_complete_event.system_shutdown_complete_event import SystemShutdownCompleteEvent


def test_systemshutdowncompleteevent_garde_ses_champs():
    success = True
    instance = SystemShutdownCompleteEvent(success=success)
    assert isinstance(instance, DomainEvent)
    assert instance.success == success


def test_systemshutdowncompleteevent_est_immuable():
    success = True
    instance = SystemShutdownCompleteEvent(success=success)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.success = success
