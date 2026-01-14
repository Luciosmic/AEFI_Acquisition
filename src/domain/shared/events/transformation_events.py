from dataclasses import dataclass
from domain.shared.events.domain_event import DomainEvent
from typing import Tuple

@dataclass(frozen=True)
class SensorTransformationAnglesUpdated(DomainEvent):
    """
    Event published when the sensor transformation angles are updated.
    """
    theta_x: float
    theta_y: float
    theta_z: float
