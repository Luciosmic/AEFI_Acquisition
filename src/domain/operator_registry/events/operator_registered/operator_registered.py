from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class OperatorRegistered(DomainEvent):
    """An operator was created in the registry (see operator_registered_intention.md)."""

    operator_id: UUID
    name: str
    registered_at: datetime
