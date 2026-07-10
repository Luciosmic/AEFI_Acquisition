from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)


@dataclass(frozen=True)
class FieldSampleAcquired(DomainEvent):
    """Event emitted when a new electric field probe sample is available."""

    probe_serial_number: str
    acquisition_id: UUID
    sample_index: int
    sample: FieldMeasurement
