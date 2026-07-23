"""
Scan Point Result Value Object

Responsibility:
- Associate a spatial position with a measurement result.
- Immutable snapshot of a single point in a scan.
"""

from dataclasses import dataclass
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

@dataclass(frozen=True)
class ScanPointResult:
    """
    Result of a single scan point.
    
    Associates WHERE (Position) with WHAT (Measurement).
    """
    position: Position2D
    measurement: AefiVoltageMeasurement
    point_index: int
