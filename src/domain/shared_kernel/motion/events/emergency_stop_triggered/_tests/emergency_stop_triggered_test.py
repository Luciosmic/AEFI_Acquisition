"""Caractérisation de emergency_stop_triggered : le comportement actuel, sans le changer."""
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.motion.events.emergency_stop_triggered.emergency_stop_triggered import EmergencyStopTriggered


def test_emergencystoptriggered_garde_ses_champs():
    instance = EmergencyStopTriggered()
    assert isinstance(instance, DomainEvent)
    assert instance is not None
