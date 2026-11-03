from dataclasses import dataclass
from typing import Union
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig


@dataclass(frozen=True)
class ScanStarted(DomainEvent):
    """Event emitted when a scan starts."""
    scan_id: UUID
    config: Union[StepScanConfig, LineScanConfig]
