"""ScanClosureFailed event (see scan_closure_failed_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanClosureFailed(DomainEvent):
    scan_id: UUID
    source: str
    acquisition_id: UUID
    reason: str
