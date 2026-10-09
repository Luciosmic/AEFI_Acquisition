"""AefiCorrectedFieldSampleAcquired event (see aefi_corrected_field_sample_acquired_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import (
    AefiCorrectedFieldMeasurement,
)


@dataclass(frozen=True)
class AefiCorrectedFieldSampleAcquired(DomainEvent):
    """Emitted once a corrected sample has been transformed from the sensor frame to
    the source frame."""

    acquisition_id: UUID
    sample_index: int
    sample: AefiCorrectedFieldMeasurement
