"""Caractérisation de frequency_point_acquired : le comportement actuel, sans le changer."""
from datetime import datetime, timezone
from uuid import UUID
import dataclasses
import pytest

from domain.frequency_sweep.events.frequency_point_acquired.frequency_point_acquired import FrequencyPointAcquired
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


def test_frequencypointacquired_garde_ses_champs() -> None:
    frequency_sweep_id = UUID(int=1)
    role = "x"
    frequency_index = 3
    frequency_hz = 1.5
    measurement = AefiVoltageMeasurement(voltage_x_in_phase=1.5, voltage_x_quadrature=1.5, voltage_y_in_phase=1.5, voltage_y_quadrature=1.5, voltage_z_in_phase=1.5, voltage_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    samples_count = 3
    table_height_mm = 1.5
    instance = FrequencyPointAcquired(frequency_sweep_id=frequency_sweep_id, role=role, frequency_index=frequency_index, frequency_hz=frequency_hz, measurement=measurement, samples_count=samples_count, table_height_mm=table_height_mm)
    assert isinstance(instance, DomainEvent)
    assert instance.frequency_sweep_id == frequency_sweep_id
    assert instance.role == role
    assert instance.frequency_index == frequency_index
    assert instance.frequency_hz == frequency_hz
    assert instance.measurement == measurement
    assert instance.samples_count == samples_count
    assert instance.table_height_mm == table_height_mm


def test_frequencypointacquired_est_immuable() -> None:
    frequency_sweep_id = UUID(int=1)
    role = "x"
    frequency_index = 3
    frequency_hz = 1.5
    measurement = AefiVoltageMeasurement(voltage_x_in_phase=1.5, voltage_x_quadrature=1.5, voltage_y_in_phase=1.5, voltage_y_quadrature=1.5, voltage_z_in_phase=1.5, voltage_z_quadrature=1.5, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    samples_count = 3
    table_height_mm = 1.5
    instance = FrequencyPointAcquired(frequency_sweep_id=frequency_sweep_id, role=role, frequency_index=frequency_index, frequency_hz=frequency_hz, measurement=measurement, samples_count=samples_count, table_height_mm=table_height_mm)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.frequency_sweep_id = frequency_sweep_id
