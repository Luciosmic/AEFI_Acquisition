from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class HardwareConfigurationControlChanged(DomainEvent):
    """The owner of one hardware's advanced configuration (e.g. "mcu" n_avg,
    "ads131a04" OSR) changed: taken by `controller`, or released (None —
    editable in the Hardware Advanced Config panel again)."""

    hardware_id: str
    controller: Optional[str]
