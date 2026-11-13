"""Caractérisation de inertial_probe_connection_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.inertial_probe.events.inertial_probe_connection_changed.inertial_probe_connection_changed import InertialProbeConnectionChanged
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_inertialprobeconnectionchanged_garde_ses_champs():
    connected = True
    instance = InertialProbeConnectionChanged(connected=connected)
    assert isinstance(instance, DomainEvent)
    assert instance.connected == connected


def test_inertialprobeconnectionchanged_est_immuable():
    connected = True
    instance = InertialProbeConnectionChanged(connected=connected)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.connected = connected
