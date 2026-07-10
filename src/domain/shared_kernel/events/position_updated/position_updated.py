from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class PositionUpdated(DomainEvent):
    """Event published when position changes."""
    position: Position2D
    is_moving: bool
