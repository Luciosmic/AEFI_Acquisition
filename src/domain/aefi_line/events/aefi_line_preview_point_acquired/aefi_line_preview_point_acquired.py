"""AefiLinePreviewPointAcquired event (see aefi_line_preview_point_acquired_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class AefiLinePreviewPointAcquired(DomainEvent):
    """PROVISIONAL: a grid point of a line still being swept. Not a fact of the
    AefiLine aggregate — the export and the counters must ignore it."""
    scan_id: UUID
    line_index: int
    index_in_line: int
    position: Position2D
    measurement: AefiVoltageMeasurement
