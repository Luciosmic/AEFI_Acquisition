"""Caractérisation de electric_field_probe_connection_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.electric_field_probes.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import ElectricFieldProbeConnectionChanged
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobeconnectionchanged_garde_ses_champs() -> None:
    connected = True
    instance = ElectricFieldProbeConnectionChanged(connected=connected)
    assert isinstance(instance, DomainEvent)
    assert instance.connected == connected


def test_electricfieldprobeconnectionchanged_est_immuable() -> None:
    connected = True
    instance = ElectricFieldProbeConnectionChanged(connected=connected)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.connected = connected  # type: ignore[misc]
