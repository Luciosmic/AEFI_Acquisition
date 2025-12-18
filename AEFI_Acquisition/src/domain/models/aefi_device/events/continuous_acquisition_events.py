"""
Continuous Acquisition Domain Events

Responsibility:
- Define events related to continuous (streaming) acquisition.

Rationale:
- Decouple continuous acquisition loop from UI, persistence and other
  side‑effects by publishing domain events.
"""

from dataclasses import dataclass
from uuid import UUID

from domain.shared.events.domain_event import DomainEvent
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement


@dataclass(frozen=True)
class ContinuousAcquisitionSampleAcquired(DomainEvent):
    """
    Event emitted when a new continuous acquisition sample is available.
    """

    acquisition_id: UUID
    sample_index: int
    sample: VoltageMeasurement


@dataclass(frozen=True)
class ContinuousAcquisitionFailed(DomainEvent):
    """
    Event emitted when the continuous acquisition loop fails (exception).
    """

    acquisition_id: UUID
    reason: str


@dataclass(frozen=True)
class ContinuousAcquisitionStopped(DomainEvent):
    """
    Event emitted when the continuous acquisition stops (normally or after failure).
    """

    acquisition_id: UUID
