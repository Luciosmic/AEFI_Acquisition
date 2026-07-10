from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig


@dataclass(frozen=True)
class ScanStarted(DomainEvent):
    """Event emitted when a scan starts."""
    scan_id: UUID
    config: StepScanConfig
