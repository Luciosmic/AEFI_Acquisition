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
    def is_acquisition_running(self) -> bool: ...

    @abstractmethod
    def refresh_battery(self) -> None:
        """
        Re-read the probe's battery level on demand. No-op if not connected
        or if an acquisition is currently running — the battery query shares
        the probe's physical link with sample acquisition and could perturb
        an in-progress stream.
        """
