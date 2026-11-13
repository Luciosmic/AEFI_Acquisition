from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class InertialProbeConnectionChanged(DomainEvent):
    """The inertial probe board connected, disconnected, or failed to connect."""

    connected: bool
    error: Optional[str] = None
