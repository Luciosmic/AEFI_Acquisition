"""Caractérisation de system_shutting_down_event : le comportement actuel, sans le changer."""
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.system_shutting_down_event.system_shutting_down_event import SystemShuttingDownEvent


def test_systemshuttingdownevent_garde_ses_champs() -> None:
    instance = SystemShuttingDownEvent()
    assert isinstance(instance, DomainEvent)
    assert instance is not None
