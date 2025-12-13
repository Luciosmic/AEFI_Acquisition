"""
Scan bounded context (Domain Model).

Responsibility:
- Provide a stable import path for the StepScan aggregate and all
  its associated value objects and events.
"""

from domain.aggregates.step_scan import StepScan
from domain.entities.spatial_scan import SpatialScan

from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.scan.scan_pattern import ScanPattern
from domain.value_objects.scan.scan_status import ScanStatus
from domain.value_objects.scan.scan_point_result import ScanPointResult
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.scan_progress import ScanProgress
from domain.value_objects.scan.scan_type import ScanType

from domain.events.scan_events import (
    ScanStarted,
    ScanPointAcquired,
    ScanCompleted,
    ScanFailed,
    ScanCancelled,
)

__all__ = [
    # Aggregates / Entities
    "StepScan",
    "SpatialScan",
    # Config / VO
    "StepScanConfig",
    "ScanZone",
    "ScanPattern",
    "ScanStatus",
    "ScanPointResult",
    "ScanTrajectory",
    "ScanProgress",
    "ScanType",
    # Events
    "ScanStarted",
    "ScanPointAcquired",
    "ScanCompleted",
    "ScanFailed",
    "ScanCancelled",
]


