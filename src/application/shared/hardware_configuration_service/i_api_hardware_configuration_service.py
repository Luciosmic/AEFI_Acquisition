from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from domain.shared_kernel.operation_result import OperationResult

from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema


class IApiHardwareConfigurationService(ABC):
    """
    Responsibility:
    - Inbound API contract for HardwareConfigurationService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by HardwareConfigurationService.
    """

    @abstractmethod
    def list_hardware_ids(self) -> List[str]: ...

    @abstractmethod
    def get_hardware_display_name(self, hardware_id: str) -> str: ...

    @abstractmethod
    def get_parameter_specs(self, hardware_id: str) -> List[HardwareAdvancedParameterSchema]: ...

    @abstractmethod
    def apply_config(self, hardware_id: str, config: Dict[str, Any]) -> OperationResult[None, str]:
        """Refused while a controller holds this hardware's configuration."""

    @abstractmethod
    def save_config_as_default(self, hardware_id: str, config: Dict[str, Any]) -> OperationResult[None, str]: ...

    @abstractmethod
    def reset_to_default(self, hardware_id: str) -> OperationResult[None, str]: ...

    @abstractmethod
    def take_control(self, hardware_id: str, controller: str) -> OperationResult[None, str]:
        """Become the only one allowed to change this hardware's configuration."""

    @abstractmethod
    def release_control(self, hardware_id: str, controller: str) -> None: ...

    @abstractmethod
    def get_controller(self, hardware_id: str) -> Optional[str]: ...
