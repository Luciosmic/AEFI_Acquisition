"""
Domain: Measurement Result

Responsibility:
    Represents the result of a measurement at a single scan point.

Rationale:
    Encapsulates the complete information about a measurement:
    position, voltage data, timing, and scan context.

Design:
    - Frozen dataclass (immutable)
    - Links position to measurement data
"""
from dataclasses import dataclass
from datetime import datetime
from domain.shared.value_objects.position_2d import Position2D
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement

@dataclass(frozen=True)
class MeasurementResult:
    """Result of a measurement at a scan point.
    
    Complete information about a single measurement:
    - Spatial position
    - Voltage measurement data
    - Timing information
    - Scan context (point/line indices)
    """
    
    # Spatial information
    position: Position2D
    
    # Measurement data
    voltage: VoltageMeasurement
    
    # Timing
    timestamp: datetime
    
    # Scan context
    point_index: int  # Index within entire scan (0-indexed)
    line_index: int   # Index of scan line (0-indexed)
    
    def __post_init__(self):
        """Validate indices."""
        if self.point_index < 0:
            raise ValueError(f"point_index must be >= 0, got {self.point_index}")
        
        if self.line_index < 0:
            raise ValueError(f"line_index must be >= 0, got {self.line_index}")

