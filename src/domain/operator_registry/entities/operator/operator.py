"""
Operator — the person who runs an acquisition (see operator_intention.md).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Operator:
    """An operator known to the registry. Identity: `operator_id`."""

    operator_id: UUID
    name: str
    registered_at: datetime
