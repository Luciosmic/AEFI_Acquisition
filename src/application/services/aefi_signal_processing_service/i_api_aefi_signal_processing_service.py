"""IApiAefiSignalProcessingService (see aefi_signal_processing_service_intention.md)."""

from abc import ABC, abstractmethod

from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)


class IApiAefiSignalProcessingService(ABC):
    """
    Responsibility:
    - Inbound API contract for AefiSignalProcessingService.
    - Defines what UI adapters and presenters may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound ports
      (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by AefiSignalProcessingService.
    """

    @abstractmethod
    def calibrate_noise(self) -> None: ...

    @abstractmethod
    def calibrate_phase(self) -> None: ...

    @abstractmethod
    def calibrate_primary(self) -> None: ...

    @abstractmethod
    def reset_calibration(self) -> None: ...

    @abstractmethod
    def set_noise_correction_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_phase_correction_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_primary_correction_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def get_calibration(self) -> AefiSignalCorrectionCalibration: ...
