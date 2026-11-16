from dataclasses import dataclass

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class AcquisitionExportOpened(DomainEvent):
    """An acquisition opened its export: its files are being written until the matching AcquisitionExportClosed."""

    acquisition_kind: str
    acquisition_id: str
    measured_object: str = ""
