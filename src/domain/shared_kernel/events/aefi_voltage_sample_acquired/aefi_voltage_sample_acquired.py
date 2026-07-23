from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


@dataclass(frozen=True)
class AefiVoltageSampleAcquired(DomainEvent):
    """
    Event emitted when a new continuous acquisition sample is available.
    """

    acquisition_id: UUID
    sample_index: int
    sample: AefiVoltageMeasurement
