from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class MeasuredObjectRegistered(DomainEvent):
    """An measured_object was created in the registry (see measured_object_registered_intention.md)."""

    measured_object_id: UUID
    name: str
    registered_at: datetime
