from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class AefiVoltageReadingStopped(DomainEvent):
    """
    Event emitted when a continuous AEFI voltage reading stops (normally or after failure).
    """

    acquisition_id: UUID
