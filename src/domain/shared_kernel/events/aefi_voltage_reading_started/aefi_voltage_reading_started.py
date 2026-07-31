from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class AefiVoltageReadingStarted(DomainEvent):
    """
    Event emitted when a continuous AEFI voltage reading starts.
    """

    acquisition_id: UUID
