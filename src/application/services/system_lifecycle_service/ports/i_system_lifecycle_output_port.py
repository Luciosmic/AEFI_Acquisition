from abc import ABC, abstractmethod
from typing import Dict, List, Any

class ISystemLifecycleOutputPort(ABC):
    """
    Output port for System Lifecycle Services.
    Allows the service to notify the UI/Environment about startup/shutdown progress
    without coupling to specific UI libraries.

    Responsibility:
        - Déclarer `present_startup_started(message)`, `present_initialization_step(subsystem, status)`, `present_error(message)`, `present_startup_completed(success, errors)`.
        - Déclarer `present_shutdown_started()`, `present_shutdown_completed(success, errors)`.

    Rationale:
        Port de sortie vers la UI pour notifier les étapes de démarrage/arrêt du système. Sans ce port, les services lifecycle devraient appeler directement des widgets Qt ou logger uniquement, sans feedback visuel.

    Design:
        - **Port outbound (output)** dans `system_lifecycle_service/`.
        - Implémenté par `PresenterSystemLifecycle` dans `interface/ui_system_lifecycle/`.
    """

    @abstractmethod
    def present_startup_started(self, config_summary: str) -> None:
        pass

    @abstractmethod
    def present_initialization_step(self, step_name: str, status: str) -> None:
        pass

    @abstractmethod
    def present_startup_completed(self, success: bool, errors: List[str]) -> None:
        pass

    @abstractmethod
    def present_shutdown_started(self) -> None:
        pass

    @abstractmethod
    def present_shutdown_step(self, step_name: str, status: str) -> None:
        pass

    @abstractmethod
    def present_shutdown_completed(self, success: bool, errors: List[str]) -> None:
        pass

    @abstractmethod
    def present_error(self, error_message: str) -> None:
        pass
