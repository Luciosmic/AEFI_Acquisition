"""
Domain Events Base Class

Responsibility:
- Base class for all domain events.
- Captures the timestamp of occurrence.
"""

from dataclasses import dataclass, field, InitVar
from typing import Optional
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    occurred_on: datetime = field(init=False, default_factory=datetime.now)
