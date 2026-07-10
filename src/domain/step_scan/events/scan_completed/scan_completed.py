from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanCompleted(DomainEvent):
    """Event emitted when a scan completes successfully."""
    scan_id: UUID
    total_points: int
