from abc import ABC, abstractmethod
from typing import Callable, Dict, Any

from .dtos.scan_dtos import Scan2DConfigDTO, ScanStatusDTO
from .ports.i_scan_output_port import IScanOutputPort
from domain.events.domain_event import DomainEvent


class IApiScanApplicationService(ABC):
    """
    Responsibility:
    - Inbound API contract for ScanApplicationService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.
    - Enables testability and future substitution of the service implementation.

    Design:
    - Pure ABC, no state.
    - Implemented by ScanApplicationService.
    """

    @abstractmethod
    def execute_scan(self, scan_dto: Scan2DConfigDTO) -> bool: ...

    @abstractmethod
    def pause_scan(self) -> None: ...

    @abstractmethod
    def resume_scan(self) -> None: ...

    @abstractmethod
    def cancel_scan(self) -> None: ...

    @abstractmethod
    def get_status(self) -> ScanStatusDTO: ...

    @abstractmethod
    def set_output_port(self, output_port: IScanOutputPort) -> None: ...

    @abstractmethod
    def subscribe_to_scan_updates(self, callback: Callable[[DomainEvent], None]) -> None: ...

    @abstractmethod
    def subscribe_to_scan_completion(self, callback: Callable[[DomainEvent], None]) -> None: ...
