from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class MotionCompleted(DomainEvent):
    """Event published when a motion is completed."""
    motion_id: str
    final_position: Position2D
    duration_ms: float
