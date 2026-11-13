"""Caractérisation de aefi_corrected_field_sample_acquired : le comportement actuel, sans le changer."""
from datetime import datetime, timezone
from uuid import UUID
import dataclasses
import pytest

from domain.aefi_signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import AefiCorrectedFieldSampleAcquired
from domain.aefi_signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import AefiCorrectedFieldMeasurement
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aeficorrectedfieldsampleacquired_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = AefiCorrectedFieldMeasurement(field_x_in_phase=1.5, field_x_quadrature=1.5, field_y_in_phase=1.5, field_y_quadrature=1.5, field_z_in_phase=1.5, field_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = AefiCorrectedFieldSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.sample_index == sample_index
    assert instance.sample == sample


def test_aeficorrectedfieldsampleacquired_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    sample = AefiCorrectedFieldMeasurement(field_x_in_phase=1.5, field_x_quadrature=1.5, field_y_in_phase=1.5, field_y_quadrature=1.5, field_z_in_phase=1.5, field_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    instance = AefiCorrectedFieldSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, sample=sample)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
