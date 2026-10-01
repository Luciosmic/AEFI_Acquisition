from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


@dataclass(frozen=True)
class ScanPointAcquired(DomainEvent):
    """Event emitted when a single point is acquired.

    `baseline_measurement` is set only in differential mode (same point,
    excitation muted). None otherwise.
    """
    scan_id: UUID
    point_index: int
    position: Position2D
    measurement: AefiVoltageMeasurement
    baseline_measurement: Optional[AefiVoltageMeasurement] = None
