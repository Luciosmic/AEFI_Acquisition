from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class MotionStarted(DomainEvent):
    """Event published when a motion starts."""
    motion_id: str
    target_position: Position2D
