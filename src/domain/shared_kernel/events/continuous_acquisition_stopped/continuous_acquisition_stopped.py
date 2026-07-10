from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ContinuousAcquisitionStopped(DomainEvent):
    """
    Event emitted when the continuous acquisition stops (normally or after failure).
    """

    acquisition_id: UUID
