"""Caractérisation de aefi_voltage_reading_stopped : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.aefi_voltage_reading_stopped.aefi_voltage_reading_stopped import AefiVoltageReadingStopped
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aefivoltagereadingstopped_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    instance = AefiVoltageReadingStopped(acquisition_id=acquisition_id)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id


def test_aefivoltagereadingstopped_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    instance = AefiVoltageReadingStopped(acquisition_id=acquisition_id)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
