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

from .domain_event import DomainEvent
from ..value_objects.acquisition.voltage_measurement import VoltageMeasurement


@dataclass(frozen=True)
class ContinuousAcquisitionSampleAcquired(DomainEvent):
    """
    Event emitted when a new continuous acquisition sample is available.
    """

    acquisition_id: UUID
    sample_index: int
    sample: VoltageMeasurement


