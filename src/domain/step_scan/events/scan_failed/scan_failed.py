from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanFailed(DomainEvent):
    """Event emitted when a scan fails."""
    scan_id: UUID
    reason: str
