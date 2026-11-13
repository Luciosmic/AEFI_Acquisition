"""Caractérisation de electric_field_probe_reading_failed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.electric_field_probes.events.electric_field_probe_reading_failed.electric_field_probe_reading_failed import ElectricFieldProbeReadingFailed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobereadingfailed_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = ElectricFieldProbeReadingFailed(acquisition_id=acquisition_id, reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.reason == reason


def test_electricfieldprobereadingfailed_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = ElectricFieldProbeReadingFailed(acquisition_id=acquisition_id, reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
