"""
Scan Point Result Value Object

Responsibility:
- Associate a spatial position with a measurement result.
- Immutable snapshot of a single point in a scan.
"""

from dataclasses import dataclass
from domain.shared.value_objects.position_2d import Position2D
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement

@dataclass(frozen=True)
class ScanPointResult:
    """
    Result of a single scan point.
    
    Associates WHERE (Position) with WHAT (Measurement).
    """
    position: Position2D
    measurement: VoltageMeasurement
    point_index: int
