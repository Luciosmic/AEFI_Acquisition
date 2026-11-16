from dataclasses import dataclass

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class AcquisitionExportClosed(DomainEvent):
    """An acquisition closed its export, whatever the outcome (end, stop, failure): nothing more is written to it."""

    acquisition_kind: str
    acquisition_id: str
