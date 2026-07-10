from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanResumed(DomainEvent):
    """Event emitted when a scan is resumed."""
    scan_id: UUID
    resume_from_point_index: int
