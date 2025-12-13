from abc import ABC, abstractmethod
from typing import Dict, List, Any

class ISystemLifecycleOutputPort(ABC):
    """
    Output port for System Lifecycle Services.
    Allows the service to notify the UI/Environment about startup/shutdown progress
    without coupling to specific UI libraries.
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
