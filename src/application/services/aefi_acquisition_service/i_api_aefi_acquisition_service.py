from abc import ABC, abstractmethod
from typing import Optional

from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from domain.shared_kernel.operation_result import OperationResult


class IApiAefiAcquisitionService(ABC):
    """
    Responsibility:
    - Inbound API contract for AefiAcquisitionService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by AefiAcquisitionService.
    - Single owner: while a controller holds the stream (take_control),
      start/stop from anyone else (controller=None = by hand) is refused.
    """

    @abstractmethod
    def take_control(self, controller: str) -> OperationResult[None, str]: ...

    @abstractmethod
    def release_control(self, controller: str) -> None: ...

    @abstractmethod
    def get_controller(self) -> Optional[str]: ...

    @abstractmethod
    def start_acquisition(
        self, config: AefiAcquisitionConfig, controller: Optional[str] = None
    ) -> OperationResult[None, str]: ...

    @abstractmethod
    def stop_acquisition(self, controller: Optional[str] = None) -> OperationResult[None, str]: ...

    @abstractmethod
    def is_acquisition_running(self) -> bool: ...
