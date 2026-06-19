from abc import ABC, abstractmethod

from application.services.continuous_acquisition_service.dtos.continuous_acquisition_dtos import ContinuousAcquisitionConfig


class IApiContinuousAcquisitionService(ABC):
    """
    Responsibility:
    - Inbound API contract for ContinuousAcquisitionService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by ContinuousAcquisitionService.
    """

    @abstractmethod
    def start_acquisition(self, config: ContinuousAcquisitionConfig) -> None: ...

    @abstractmethod
    def stop_acquisition(self) -> None: ...

    @abstractmethod
    def update_acquisition_parameters(self, config: ContinuousAcquisitionConfig) -> None: ...
