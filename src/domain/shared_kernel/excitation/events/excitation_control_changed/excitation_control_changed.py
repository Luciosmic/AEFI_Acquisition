from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ExcitationControlChanged(DomainEvent):
    """The owner of the excitation changed: taken by `controller` (readable
    name, e.g. "scan"), or released (None — settable by hand again)."""

    controller: Optional[str]
