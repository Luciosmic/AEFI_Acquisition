"""Caractérisation de aefi_voltage_reading_started : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.aefi_voltage_reading_started.aefi_voltage_reading_started import AefiVoltageReadingStarted
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aefivoltagereadingstarted_garde_ses_champs():
    acquisition_id = UUID(int=1)
    instance = AefiVoltageReadingStarted(acquisition_id=acquisition_id)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id


def test_aefivoltagereadingstarted_est_immuable():
    acquisition_id = UUID(int=1)
    instance = AefiVoltageReadingStarted(acquisition_id=acquisition_id)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
