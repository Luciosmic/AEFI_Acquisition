from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class AefiAcquisitionControlChanged(DomainEvent):
    """The owner of the AEFI continuous acquisition stream changed: taken by
    `controller` (readable name, e.g. "scan"), or released (None — Start/Stop
    by hand again)."""

    controller: Optional[str]
