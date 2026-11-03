"""AefiLineAcquired event (see aefi_line_acquired_intention.md)."""

from dataclasses import dataclass
from typing import Tuple
from uuid import UUID

from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId
from domain.aefi_line.value_objects.line_grid_point.line_grid_point import LineGridPoint
from domain.shared_kernel.events.domain_event import DomainEvent

VOLT_UNIT_URI = "http://qudt.org/vocab/unit/V"
AEFI_LINE_SOURCE = "aefi_line"


@dataclass(frozen=True)
class AefiLineAcquired(DomainEvent):
    aefi_line_id: AefiLineId
    scan_id: UUID
    line_index: int
    points: Tuple[LineGridPoint, ...]
    points_count: int
    measurement_unit: str = VOLT_UNIT_URI

    @property
    def source(self) -> str:
        return AEFI_LINE_SOURCE

    @property
    def acquisition_id(self) -> UUID:
        return self.aefi_line_id
