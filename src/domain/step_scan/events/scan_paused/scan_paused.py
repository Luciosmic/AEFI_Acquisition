from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanPaused(DomainEvent):
    """Event emitted when a scan is paused."""
    scan_id: UUID
    current_point_index: int
