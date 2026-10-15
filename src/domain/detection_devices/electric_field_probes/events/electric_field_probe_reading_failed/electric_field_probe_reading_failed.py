from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ElectricFieldProbeReadingFailed(DomainEvent):
    """
    Event emitted when a continuous electric field probe reading loop fails (exception).
    """

    acquisition_id: UUID
    reason: str
