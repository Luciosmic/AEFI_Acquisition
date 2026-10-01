"""
Domain Events Base Class

Responsibility:
- Base class for all domain events.
- Captures the timestamp of occurrence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc), kw_only=True)
    event_id: UUID = field(default_factory=uuid4, kw_only=True)
