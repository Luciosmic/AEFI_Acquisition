"""Caractérisation de field_sample_acquired : le comportement actuel, sans le changer."""
from datetime import datetime, timezone
from uuid import UUID
import dataclasses
import pytest

from domain.electric_field_probes.events.field_sample_acquired.field_sample_acquired import FieldSampleAcquired
from domain.electric_field_probes.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_fieldsampleacquired_garde_ses_champs() -> None:
    probe_serial_number = "x"
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = FieldMeasurement(components=(1.5,), timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = FieldSampleAcquired(probe_serial_number=probe_serial_number, acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    assert isinstance(instance, DomainEvent)
    assert instance.probe_serial_number == probe_serial_number
    assert instance.acquisition_id == acquisition_id
    assert instance.sample_index == sample_index
    assert instance.sample == sample


def test_fieldsampleacquired_est_immuable() -> None:
    probe_serial_number = "x"
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = FieldMeasurement(components=(1.5,), timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = FieldSampleAcquired(probe_serial_number=probe_serial_number, acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.probe_serial_number = probe_serial_number  # type: ignore[misc]
