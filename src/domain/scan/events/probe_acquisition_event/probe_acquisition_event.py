"""ProbeAcquisitionEvent contract (see probe_acquisition_event_intention.md)."""

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class ProbeAcquisitionEvent(Protocol):
    @property
    def scan_id(self) -> UUID: ...

    @property
    def source(self) -> str: ...

    @property
    def acquisition_id(self) -> UUID: ...
