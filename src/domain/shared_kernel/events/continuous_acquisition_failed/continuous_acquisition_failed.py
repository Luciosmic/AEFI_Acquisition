from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ContinuousAcquisitionFailed(DomainEvent):
    """
    Event emitted when the continuous acquisition loop fails (exception).
    """

    acquisition_id: UUID
    reason: str
