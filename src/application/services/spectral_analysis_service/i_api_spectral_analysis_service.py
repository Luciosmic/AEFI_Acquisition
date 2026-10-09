"""IApiSpectralAnalysisService (see spectral_analysis_service_intention.md)."""

from abc import ABC, abstractmethod

from .dtos.spectral_analysis_dtos import SetWindowDurationDTO


class IApiSpectralAnalysisService(ABC):
    """
    Responsibility:
    - Inbound API contract for SpectralAnalysisService.
    - Defines what UI adapters and presenters may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound ports
      (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by SpectralAnalysisService.
    """

    @abstractmethod
    def set_window_duration(self, dto: SetWindowDurationDTO) -> None: ...

    @abstractmethod
    def get_window_duration(self) -> float: ...
