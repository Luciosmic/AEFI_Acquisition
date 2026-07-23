"""
Domain: Acquisition - AEFI Voltage Measurement

Responsibility:
    Represents a single AEFI measurement: the phase-sensitive (in-phase /
    quadrature) voltage reading produced by the AEFI's own synchronous
    detection chain (ADS131A04, phase-referenced to the AD9106 excitation).
    Uses ubiquitous language (domain terminology) instead of hardware channels.

Rationale:
    Encapsulates the 6 voltage components (X, Y, Z in-phase and quadrature)
    measured by the ADC. Immutable value object with timestamp. Named
    explicitly for AEFI (rather than a generic "voltage measurement") because
    it is not just any voltage reading — it's the AEFI's own synchronous
    detection, distinct from the electric field probe's amplitude-only
    FieldMeasurement (no phase reference).

Design:
    - Frozen dataclass (immutable)
    - Domain language: voltage_x_in_phase instead of adc1_ch1
    - Mapping to hardware done in infrastructure layer
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class AefiVoltageMeasurement:
    """AEFI voltage measurement: phase-sensitive reading from the AEFI's
    synchronous detection chain.

    Represents the 6 components of the AEFI measurement:
    - X, Y, Z directions
    - In-phase and quadrature components for each direction, relative to
      the AD9106 excitation phase reference

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

