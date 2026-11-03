"""AefiPointAcquired event (see aefi_point_acquired_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D

VOLT_UNIT_URI = "http://qudt.org/vocab/unit/V"
AEFI_POINT_SOURCE = "aefi_point"


@dataclass(frozen=True)
class AefiPointAcquired(DomainEvent):
    aefi_point_id: AefiPointId
    scan_id: UUID
    position: Position2D
    measurement: AefiVoltageMeasurement
    samples_count: int
    measurement_unit: str = VOLT_UNIT_URI

    @property
    def source(self) -> str:
        return AEFI_POINT_SOURCE

    @property
    def acquisition_id(self) -> UUID:
        return self.aefi_point_id
