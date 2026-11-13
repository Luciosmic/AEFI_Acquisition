"""Caractérisation de system_ready_event : le comportement actuel, sans le changer."""
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.system_ready_event.system_ready_event import SystemReadyEvent


def test_systemreadyevent_garde_ses_champs():
    instance = SystemReadyEvent()
    assert isinstance(instance, DomainEvent)
    assert instance is not None
