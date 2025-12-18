"""
Hardware Configuration Provider Port

Responsibility:
- Define an abstract interface for discovering hardware configuration parameters
- Allow application services to query available hardware and its actionable parameters
  without depending on concrete infrastructure implementations

Rationale:
- Hexagonal Architecture: application depends on ports, infrastructure on adapters
- Centralizes how hardware declares its configurable parameters
- Enables testing with mock hardware providers

Design:
- Protocol-like interface (duck-typing friendly)
- Implemented by infrastructure hardware adapters
- Exposes ActionableHardwareParametersSpec list for each hardware
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from domain.shared.value_objects.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema


class IHardwareAdvancedConfigurator(ABC):
    """
    Port interface for Advanced Hardware Configuration.

    Responsibility:
    - Allow users to access and modify "Advanced" hardware parameters.
    - These are typically low-level settings (PID gains, register values)
      that the Domain layer usually abstracts away.
    - This interface allows a generic UI to expose these settings without
      hard-coupling to specific hardware.
    """

    @property
    @abstractmethod
    def hardware_id(self) -> str:
        """
        Stable identifier for the hardware.

        Responsibility:
        - Unique key used by application services to reference this hardware

        Example:
        - "arcus_performax_4ex"
        - "ad9106_dds"
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for the hardware.

        Used by UI when listing available hardware.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        """
        Return actionable parameter specifications for this hardware.

        Returns:
            List of HardwareAdvancedParameterSchema
        """
        raise NotImplementedError

    @abstractmethod
    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration values to the underlying hardware.

        Responsibility:
        - Bridge high-level config dictionaries to concrete hardware APIs

        Args:
            config: Dictionary of parameter values keyed by spec.name
        """
        raise NotImplementedError

    @abstractmethod
    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save the provided configuration as the new default configuration.

        Responsibility:
        - Persist the configuration to a storage (e.g., JSON file) so it is loaded on next startup.

        Args:
            config: Dictionary of parameter values keyed by spec.name
        """
        raise NotImplementedError
