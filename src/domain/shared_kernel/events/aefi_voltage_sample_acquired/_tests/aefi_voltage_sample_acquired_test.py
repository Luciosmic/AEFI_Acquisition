"""Caractérisation de aefi_voltage_sample_acquired : le comportement actuel, sans le changer."""
from datetime import datetime, timezone
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import AefiVoltageSampleAcquired
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


def test_aefivoltagesampleacquired_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = AefiVoltageMeasurement(voltage_x_in_phase=1.5, voltage_x_quadrature=1.5, voltage_y_in_phase=1.5, voltage_y_quadrature=1.5, voltage_z_in_phase=1.5, voltage_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.sample_index == sample_index
    assert instance.sample == sample


def test_aefivoltagesampleacquired_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = AefiVoltageMeasurement(voltage_x_in_phase=1.5, voltage_x_quadrature=1.5, voltage_y_in_phase=1.5, voltage_y_quadrature=1.5, voltage_z_in_phase=1.5, voltage_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
