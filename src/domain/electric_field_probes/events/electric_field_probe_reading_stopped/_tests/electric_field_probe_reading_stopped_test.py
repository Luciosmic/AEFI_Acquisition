"""Caractérisation de electric_field_probe_reading_stopped : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.electric_field_probes.events.electric_field_probe_reading_stopped.electric_field_probe_reading_stopped import ElectricFieldProbeReadingStopped
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobereadingstopped_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    instance = ElectricFieldProbeReadingStopped(acquisition_id=acquisition_id)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id


def test_electricfieldprobereadingstopped_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    instance = ElectricFieldProbeReadingStopped(acquisition_id=acquisition_id)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id  # type: ignore[misc]
