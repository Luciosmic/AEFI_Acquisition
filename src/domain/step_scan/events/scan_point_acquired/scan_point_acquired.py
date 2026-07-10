from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.voltage_measurement import VoltageMeasurement


@dataclass(frozen=True)
class ScanPointAcquired(DomainEvent):
    """Event emitted when a single point is acquired."""
    scan_id: UUID
    point_index: int
    position: Position2D
    measurement: VoltageMeasurement
