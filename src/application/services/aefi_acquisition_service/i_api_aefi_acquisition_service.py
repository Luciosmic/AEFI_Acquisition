from abc import ABC, abstractmethod

from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig


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
    """

    @abstractmethod
    def start_acquisition(self, config: AefiAcquisitionConfig) -> None: ...

    @abstractmethod
    def stop_acquisition(self) -> None: ...

    @abstractmethod
    def update_acquisition_parameters(self, config: AefiAcquisitionConfig) -> None: ...

    @abstractmethod
    def is_acquisition_running(self) -> bool: ...
