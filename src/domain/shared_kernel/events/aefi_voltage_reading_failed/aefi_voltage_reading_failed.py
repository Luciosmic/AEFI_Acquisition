from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class AefiVoltageReadingFailed(DomainEvent):
    """
    Event emitted when a continuous AEFI voltage reading loop fails (exception).
    """

    acquisition_id: UUID
    reason: str
