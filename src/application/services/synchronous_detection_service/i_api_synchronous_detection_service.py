from abc import ABC, abstractmethod

from application.services.synchronous_detection_service.dtos.sphere_phases_dto import SpherePhasesDTO


class IApiSynchronousDetectionService(ABC):
    """
    Responsibility:
    - Inbound API contract for SynchronousDetectionService.
    - Defines what UI adapters and presenters may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound ports
      (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by SynchronousDetectionService.
    """

    @abstractmethod
    def get_sphere_phases(self) -> SpherePhasesDTO: ...

    @abstractmethod
    def save_calibration_point(self) -> None: ...

    @abstractmethod
    def is_compensation_enabled(self) -> bool: ...

    @abstractmethod
    def set_compensation_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def enable_lock_in_detection(self) -> None: ...

    @abstractmethod
    def disable_lock_in_detection(self) -> None: ...

    @abstractmethod
    def set_manual_phase_offset(self, offset_degrees: float) -> None: ...

    @abstractmethod
    def reset_phase_offset_to_calibrated(self) -> None: ...
