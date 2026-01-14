"""
Motion Domain Events
"""

from dataclasses import dataclass
from .domain_event import DomainEvent
from ..value_objects.geometric.position_2d import Position2D

@dataclass(frozen=True)
class MotionStarted(DomainEvent):
    """Event published when a motion starts."""
    motion_id: str
    target_position: Position2D

@dataclass(frozen=True)
class MotionCompleted(DomainEvent):
    """Event published when a motion is completed."""
    motion_id: str
    final_position: Position2D
    duration_ms: float

@dataclass(frozen=True)
class MotionFailed(DomainEvent):
    """Event published when a motion fails."""
    motion_id: str
    error: str

@dataclass(frozen=True)
class PositionUpdated(DomainEvent):
    """Event published when position changes."""
    position: Position2D
    is_moving: bool

@dataclass(frozen=True)
class MotionStopped(DomainEvent):
    """Event published when motion is stopped (regular stop with deceleration)."""
    reason: str  # e.g., "scan_cancelled", "user_requested"

@dataclass(frozen=True)
class EmergencyStopTriggered(DomainEvent):
    """Event published when emergency stop is triggered (immediate halt)."""
    pass
