"""
MeasuredObject — the person who runs an acquisition (see measured_object_intention.md).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class MeasuredObject:
    """An measured_object known to the registry. Identity: `measured_object_id`."""

    measured_object_id: UUID
    name: str
    registered_at: datetime
