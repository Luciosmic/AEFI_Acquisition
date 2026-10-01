from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ElectricFieldProbeReadingStopped(DomainEvent):
    """
    Event emitted when a continuous electric field probe reading stops (normally or after failure).
    """

    acquisition_id: UUID
