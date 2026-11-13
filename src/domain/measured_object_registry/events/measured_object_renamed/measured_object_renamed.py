from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class MeasuredObjectRenamed(DomainEvent):
    """A measured object of the registry got a new name (see measured_object_renamed_intention.md)."""

    measured_object_id: UUID
    previous_name: str
    name: str
    renamed_at: datetime
