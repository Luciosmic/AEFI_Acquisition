"""Caractérisation de electric_field_probe_reading_started : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.electric_field_probes.events.electric_field_probe_reading_started.electric_field_probe_reading_started import ElectricFieldProbeReadingStarted
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobereadingstarted_garde_ses_champs():
    acquisition_id = UUID(int=1)
    instance = ElectricFieldProbeReadingStarted(acquisition_id=acquisition_id)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id


def test_electricfieldprobereadingstarted_est_immuable():
    acquisition_id = UUID(int=1)
    instance = ElectricFieldProbeReadingStarted(acquisition_id=acquisition_id)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
