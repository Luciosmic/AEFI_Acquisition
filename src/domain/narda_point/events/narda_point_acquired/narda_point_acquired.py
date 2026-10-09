"""NardaPointAcquired event (see narda_point_acquired_intention.md)."""

from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D

VOLT_PER_METRE_UNIT_URI = "http://qudt.org/vocab/unit/V-PER-M"
NARDA_POINT_SOURCE = "narda_point"


@dataclass(frozen=True)
class NardaPointAcquired(DomainEvent):
    narda_point_id: NardaPointId
    scan_id: UUID
    point_index: int
    position: Position2D
    field_measurement: FieldMeasurement
    baseline_field_measurement: Optional[FieldMeasurement]
    axis_labels: Optional[Tuple[str, ...]]
    samples_count: int
    measurement_unit: str = VOLT_PER_METRE_UNIT_URI

    @property
    def source(self) -> str:
        return NARDA_POINT_SOURCE

    @property
    def acquisition_id(self) -> UUID:
        return self.narda_point_id
