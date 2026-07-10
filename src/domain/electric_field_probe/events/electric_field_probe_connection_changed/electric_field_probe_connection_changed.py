from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe


@dataclass(frozen=True)
class ElectricFieldProbeConnectionChanged(DomainEvent):
    """Event emitted when the electric field probe connects, disconnects, or fails to connect."""

    connected: bool
    probe: Optional[ElectricFieldProbe] = None
    error: Optional[str] = None
