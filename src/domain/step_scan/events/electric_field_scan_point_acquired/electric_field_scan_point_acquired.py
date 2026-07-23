from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)


@dataclass(frozen=True)
class ElectricFieldScanPointAcquired(DomainEvent):
    """Event emitted when an electric field measurement is acquired at a scan point."""
    scan_id: UUID
    point_index: int
    position: Position2D
    field_measurement: FieldMeasurement
