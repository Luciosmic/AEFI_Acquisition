"""Tests for VoltageMeasurement value object."""
import pytest
from datetime import datetime
from .voltage_measurement import VoltageMeasurement

def test_voltage_measurement_creation():
    """Test creating a valid voltage measurement."""
    now = datetime.now()
    measurement = VoltageMeasurement(
        voltage_x_in_phase=1.5,
        voltage_x_quadrature=0.3,
        voltage_y_in_phase=2.1,
        voltage_y_quadrature=-0.5,
        voltage_z_in_phase=0.8,
        voltage_z_quadrature=1.2,
        timestamp=now
    )
    
    assert measurement.voltage_x_in_phase == 1.5
    assert measurement.voltage_x_quadrature == 0.3
    assert measurement.timestamp == now

def test_voltage_measurement_immutable():
    """Test that voltage measurement is immutable."""
    measurement = VoltageMeasurement(
        voltage_x_in_phase=1.0,
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=0.0,
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=0.0,
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    with pytest.raises(AttributeError):
        measurement.voltage_x_in_phase = 2.0

def test_voltage_measurement_rejects_nan():
    """Test that NaN values are rejected."""
    with pytest.raises(ValueError, match="must be finite"):
        VoltageMeasurement(
            voltage_x_in_phase=float('nan'),
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )

def test_voltage_measurement_rejects_inf():
    """Test that infinite values are rejected."""
    with pytest.raises(ValueError, match="must be finite"):
        VoltageMeasurement(
            voltage_x_in_phase=float('inf'),
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )

def test_voltage_measurement_accepts_zero():
    """Test that zero values are accepted."""
    measurement = VoltageMeasurement(
        voltage_x_in_phase=0.0,
        voltage_x_quadrature=0.0,
        voltage_y_in_phase=0.0,
        voltage_y_quadrature=0.0,
        voltage_z_in_phase=0.0,
        voltage_z_quadrature=0.0,
        timestamp=datetime.now()
    )
    
    assert measurement.voltage_x_in_phase == 0.0

def test_voltage_measurement_accepts_negative():
    """Test that negative values are accepted."""
    measurement = VoltageMeasurement(
        voltage_x_in_phase=-1.5,
        voltage_x_quadrature=-0.3,
        voltage_y_in_phase=-2.1,
        voltage_y_quadrature=-0.5,
        voltage_z_in_phase=-0.8,
        voltage_z_quadrature=-1.2,
        timestamp=datetime.now()
    )
    
    assert measurement.voltage_x_in_phase == -1.5

