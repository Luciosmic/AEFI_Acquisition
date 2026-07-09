from abc import ABC, abstractmethod

from application.services.system_lifecycle_service.system_lifecycle_service import (
    StartupConfig,
    StartupResult,
    ShutdownConfig,
    ShutdownResult,
)


class IApiSystemLifecycleService(ABC):
    """
    Responsibility:
    - Inbound API contract for SystemLifecycleService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by SystemLifecycleService.
    """

    @abstractmethod
    def startup_system(self, config: StartupConfig) -> StartupResult: ...

    @abstractmethod
    def shutdown_system(self, config: ShutdownConfig) -> ShutdownResult: ...
