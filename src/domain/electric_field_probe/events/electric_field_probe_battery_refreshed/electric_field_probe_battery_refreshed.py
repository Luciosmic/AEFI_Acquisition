from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe


@dataclass(frozen=True)
class ElectricFieldProbeBatteryRefreshed(DomainEvent):
    """Event emitted when an on-demand battery re-read updates the connected probe's state."""

    probe: ElectricFieldProbe
