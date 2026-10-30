from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class InertialSensorConnectionChanged(DomainEvent):
    """The inertial sensor board connected, disconnected, or failed to connect."""

    connected: bool
    error: Optional[str] = None
