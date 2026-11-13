"""Caractérisation de electric_field_probe_battery_refreshed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.electric_field_probes.electric_field_probe import ElectricFieldProbe
from domain.electric_field_probes.events.electric_field_probe_battery_refreshed.electric_field_probe_battery_refreshed import ElectricFieldProbeBatteryRefreshed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobebatteryrefreshed_garde_ses_champs() -> None:
    probe = ElectricFieldProbe(brand="x", model="x", serial_number="x", axis_labels=("x",))
    instance = ElectricFieldProbeBatteryRefreshed(probe=probe)
    assert isinstance(instance, DomainEvent)
    assert instance.probe == probe


def test_electricfieldprobebatteryrefreshed_est_immuable() -> None:
    probe = ElectricFieldProbe(brand="x", model="x", serial_number="x", axis_labels=("x",))
    instance = ElectricFieldProbeBatteryRefreshed(probe=probe)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.probe = probe  # type: ignore[misc]
