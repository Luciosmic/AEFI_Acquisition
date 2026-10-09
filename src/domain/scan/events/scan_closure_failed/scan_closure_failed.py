"""ScanClosureFailed event (see scan_closure_failed_intention.md)."""

from dataclasses import dataclass
from uuid import UUID

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ScanClosureFailed(DomainEvent):
    scan_id: UUID
    aefi_point_id: AefiPointId
    reason: str
