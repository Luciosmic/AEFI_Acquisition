"""Caractérisation de aefi_voltage_reading_failed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.aefi_voltage_reading_failed.aefi_voltage_reading_failed import AefiVoltageReadingFailed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aefivoltagereadingfailed_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = AefiVoltageReadingFailed(acquisition_id=acquisition_id, reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.reason == reason


def test_aefivoltagereadingfailed_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = AefiVoltageReadingFailed(acquisition_id=acquisition_id, reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
