from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class MeasuredObjectDeleted(DomainEvent):
    """A measured object was removed from the registry (see measured_object_deleted_intention.md)."""

    measured_object_id: UUID
    name: str
    deleted_at: datetime
