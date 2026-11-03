"""Tests for AefiCorrectedFieldMeasurement value object."""
import pytest
from datetime import datetime

from domain.signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import (
    AefiCorrectedFieldMeasurement,
)


def test_creation():
    now = datetime.now()
    measurement = AefiCorrectedFieldMeasurement(
        field_x_in_phase=1.5,
        field_x_quadrature=0.3,
        field_y_in_phase=2.1,
        field_y_quadrature=-0.5,
        field_z_in_phase=0.8,
        field_z_quadrature=1.2,
        timestamp=now,
    )

    assert measurement.field_x_in_phase == 1.5
    assert measurement.field_x_quadrature == 0.3
    assert measurement.timestamp == now


def test_immutable():
    measurement = AefiCorrectedFieldMeasurement(
        field_x_in_phase=1.0, field_x_quadrature=0.0,
        field_y_in_phase=0.0, field_y_quadrature=0.0,
        field_z_in_phase=0.0, field_z_quadrature=0.0,
        timestamp=datetime.now(),
    )

    with pytest.raises(AttributeError):
        measurement.field_x_in_phase = 2.0


def test_rejects_nan():
    with pytest.raises(ValueError, match="must be finite"):
        AefiCorrectedFieldMeasurement(
            field_x_in_phase=float('nan'), field_x_quadrature=0.0,
            field_y_in_phase=0.0, field_y_quadrature=0.0,
            field_z_in_phase=0.0, field_z_quadrature=0.0,
            timestamp=datetime.now(),
        )


def test_rejects_inf():
    with pytest.raises(ValueError, match="must be finite"):
        AefiCorrectedFieldMeasurement(
            field_x_in_phase=float('inf'), field_x_quadrature=0.0,
            field_y_in_phase=0.0, field_y_quadrature=0.0,
            field_z_in_phase=0.0, field_z_quadrature=0.0,
            timestamp=datetime.now(),
        )


def test_accepts_zero():
    measurement = AefiCorrectedFieldMeasurement(
        field_x_in_phase=0.0, field_x_quadrature=0.0,
        field_y_in_phase=0.0, field_y_quadrature=0.0,
        field_z_in_phase=0.0, field_z_quadrature=0.0,
        timestamp=datetime.now(),
    )

    assert measurement.field_x_in_phase == 0.0


def test_accepts_negative():
    measurement = AefiCorrectedFieldMeasurement(
        field_x_in_phase=-1.5, field_x_quadrature=-0.3,
        field_y_in_phase=-2.1, field_y_quadrature=-0.5,
        field_z_in_phase=-0.8, field_z_quadrature=-1.2,
        timestamp=datetime.now(),
    )

    assert measurement.field_x_in_phase == -1.5
