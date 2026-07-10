from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanCancelled(DomainEvent):
    """Event emitted when a scan is cancelled."""
    scan_id: UUID
