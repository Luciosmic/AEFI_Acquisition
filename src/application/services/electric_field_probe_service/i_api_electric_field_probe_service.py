from abc import ABC, abstractmethod

from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)


class IApiElectricFieldProbeService(ABC):
    """
    Responsibility:
    - Inbound API contract for ElectricFieldProbeService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound
      ports (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by ElectricFieldProbeService.
    """

    @abstractmethod
    def connect_probe(self) -> None:
        """Connect to the probe. Never raises — reports outcome via domain event."""

    @abstractmethod
    def disconnect_probe(self) -> None: ...

    @abstractmethod
    def start_acquisition(
        self, config: ElectricFieldProbeAcquisitionConfig
    ) -> None: ...

    @abstractmethod
    def stop_acquisition(self) -> None: ...

    @abstractmethod
    def update_acquisition_parameters(
        self, config: ElectricFieldProbeAcquisitionConfig
    ) -> None: ...
