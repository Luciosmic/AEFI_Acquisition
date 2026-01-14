"""
Scan bounded context (Domain Model).

Responsibility:
- Provide a stable import path for the StepScan aggregate and all
  its associated value objects and events.
"""

from domain.models.scan.aggregates.step_scan import StepScan
from domain.models.scan.aggregates.spatial_scan import SpatialScan
from domain.models.scan.entities.atomic_motion import AtomicMotion

from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.models.scan.value_objects.scan_trajectory import ScanTrajectory
from domain.models.scan.value_objects.scan_progress import ScanProgress
from domain.models.scan.value_objects.scan_type import ScanType
from domain.models.scan.value_objects.motion_state import MotionState

from domain.models.scan.events.scan_events import (
    ScanStarted,
    ScanPointAcquired,
    ScanCompleted,
    ScanFailed,
    ScanCancelled,
)

from domain.models.scan.events.motion_events import (
    MotionStarted,
    MotionCompleted,
    MotionFailed,
    PositionUpdated,
    MotionStopped,
    EmergencyStopTriggered,
)

from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory

__all__ = [
    # Aggregates / Entities
    "StepScan",
    "SpatialScan",
    "AtomicMotion",
    # Config / VO
    "StepScanConfig",
    "ScanZone",
    "ScanPattern",
    "ScanStatus",
    "ScanPointResult",
    "ScanTrajectory",
    "ScanProgress",
    "ScanType",
    "MotionState",
    # Services
    "MotionProfileSelector",
    "ScanTrajectoryFactory",
    # Events
    "ScanStarted",
    "ScanPointAcquired",
    "ScanCompleted",
    "ScanFailed",
    "ScanCancelled",
    "MotionStarted",
    "MotionCompleted",
    "MotionFailed",
    "PositionUpdated",
    "MotionStopped",
    "EmergencyStopTriggered",
]



