"""
Scan Domain Events

Responsibility:
- Define events related to the Scan lifecycle and execution.
- Used to decouple the domain from side effects (UI updates, logging, etc.).
"""

from dataclasses import dataclass
from uuid import UUID
from .domain_event import DomainEvent
from ..value_objects.scan.step_scan_config import StepScanConfig
from ..value_objects.geometric.position_2d import Position2D
from ..value_objects.acquisition.voltage_measurement import VoltageMeasurement

@dataclass(frozen=True)
class ScanStarted(DomainEvent):
    """Event emitted when a scan starts."""
    scan_id: UUID
    config: StepScanConfig

@dataclass(frozen=True)
class ScanPointAcquired(DomainEvent):
    """Event emitted when a single point is acquired."""
    scan_id: UUID
    point_index: int
    position: Position2D
    measurement: VoltageMeasurement

@dataclass(frozen=True)
class ScanCompleted(DomainEvent):
    """Event emitted when a scan completes successfully."""
    scan_id: UUID
    total_points: int

@dataclass(frozen=True)
class ScanFailed(DomainEvent):
    """Event emitted when a scan fails."""
    scan_id: UUID
    reason: str

@dataclass(frozen=True)
class ScanCancelled(DomainEvent):
    """Event emitted when a scan is cancelled."""
    scan_id: UUID

@dataclass(frozen=True)
class ScanPaused(DomainEvent):
    """Event emitted when a scan is paused."""
    scan_id: UUID
    current_point_index: int

@dataclass(frozen=True)
class ScanResumed(DomainEvent):
    """Event emitted when a scan is resumed."""
    scan_id: UUID
    resume_from_point_index: int
