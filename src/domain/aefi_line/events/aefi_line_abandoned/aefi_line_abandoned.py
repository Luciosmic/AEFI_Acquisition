"""AefiLineAbandoned event (see aefi_line_abandoned_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class AefiLineAbandoned(DomainEvent):
    scan_id: UUID
    line_index: int
    reason: str
    discarded_points: int
