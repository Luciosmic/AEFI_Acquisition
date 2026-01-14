"""
Domain: Acquisition - Voltage Measurement

Responsibility:
    Represents a single voltage measurement from the electric field sensor.
    Uses ubiquitous language (domain terminology) instead of hardware channels.

Rationale:
    Encapsulates the 6 voltage components (X, Y, Z in-phase and quadrature)
    measured by the ADC. Immutable value object with timestamp.

Design:
    - Frozen dataclass (immutable)
    - Domain language: voltage_x_in_phase instead of adc1_ch1
    - Mapping to hardware done in infrastructure layer
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class VoltageMeasurement:
    """Voltage measurement from electric field sensor.
    
    Represents the 6 components of the electric field measurement:
    - X, Y, Z directions
    - In-phase and quadrature components for each direction
    
    Mapping to ADC channels (done in infrastructure):
    - voltage_x_in_phase = ADC1_Ch1
    - voltage_x_quadrature = ADC1_Ch2
    - voltage_y_in_phase = ADC1_Ch3
    - voltage_y_quadrature = ADC1_Ch4
    - voltage_z_in_phase = ADC2_Ch1
    - voltage_z_quadrature = ADC2_Ch2
    """
    
    # X direction
    voltage_x_in_phase: float  # Volts
    voltage_x_quadrature: float  # Volts
    
    # Y direction
    voltage_y_in_phase: float  # Volts
    voltage_y_quadrature: float  # Volts
    
    # Z direction
    voltage_z_in_phase: float  # Volts
    voltage_z_quadrature: float  # Volts
    
    # Metadata
    timestamp: datetime
    
    # Quality metric (optional)
    uncertainty_estimate_volts: Optional[float] = None  # Estimated measurement uncertainty (±V)
    
    # Statistical Metadata (optional, for averaged measurements)
    std_dev_x_in_phase: Optional[float] = None
    std_dev_x_quadrature: Optional[float] = None
    std_dev_y_in_phase: Optional[float] = None
    std_dev_y_quadrature: Optional[float] = None
    std_dev_z_in_phase: Optional[float] = None
    std_dev_z_quadrature: Optional[float] = None
    
    def __post_init__(self):
        """Validate voltage values are finite."""
        import math
        for field_name in ['voltage_x_in_phase', 'voltage_x_quadrature',
                          'voltage_y_in_phase', 'voltage_y_quadrature',
                          'voltage_z_in_phase', 'voltage_z_quadrature']:
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value}")

