"""Caractérisation de system_startup_failed_event : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.system_startup_failed_event.system_startup_failed_event import SystemStartupFailedEvent


def test_systemstartupfailedevent_garde_ses_champs() -> None:
    reason = "x"
    instance = SystemStartupFailedEvent(reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.reason == reason


def test_systemstartupfailedevent_est_immuable() -> None:
    reason = "x"
    instance = SystemStartupFailedEvent(reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.reason = reason
