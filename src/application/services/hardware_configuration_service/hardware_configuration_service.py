"""
Hardware Configuration Service

Responsibility:
- Aggregate hardware configuration providers
- Expose available hardware and their actionable parameter specs to the UI layer

Rationale:
- Application layer needs a single entry point to query configured hardware
- Keeps UI and domain code independent from concrete infrastructure packages

Design:
- Wraps a collection of IHardwareConfigProvider instances
- Provides simple query methods (list hardware, get specs by id)
"""

from typing import Any, Dict, List

from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema
from .i_hardware_advanced_configurator import IHardwareAdvancedConfigurator


class HardwareConfigurationService:
    """
    Application-level service for hardware configuration discovery.
    """

    def __init__(self, providers: List[IHardwareAdvancedConfigurator]) -> None:
        """
        Initialize the service with a list of advanced configurators (injected from composition root).

        Args:
            providers: Concrete implementations of IHardwareAdvancedConfigurator
        """
        self._providers_by_id: Dict[str, IHardwareAdvancedConfigurator] = {
            provider.hardware_id: provider for provider in providers
        }

    def list_hardware_ids(self) -> List[str]:
        """
        List all known hardware identifiers.

        Returns:
            List of hardware_id strings
        """
        return list(self._providers_by_id.keys())

    def get_hardware_display_name(self, hardware_id: str) -> str:
        """
        Get the human-readable name for a given hardware id.

        Raises:
            KeyError: if hardware_id is unknown
        """
        return self._providers_by_id[hardware_id].display_name

    def get_parameter_specs(self, hardware_id: str) -> List[HardwareAdvancedParameterSchema]:
        """
        Get actionable parameter specifications for the given hardware.

        Raises:
            KeyError: if hardware_id is unknown
        """
        provider = self._providers_by_id[hardware_id]
        # Call static method on the class, not the instance
        return type(provider).get_parameter_specs()

    def apply_config(self, hardware_id: str, config: Dict[str, Any]) -> None:
        """
        Apply configuration values to a specific hardware device.

        Responsibility:
        - Route high-level configuration (dict) to the appropriate
          hardware configuration provider.

        Args:
            hardware_id: Identifier of the target hardware
            config: Dictionary of parameter values keyed by spec.name

        Raises:
            KeyError: if hardware_id is unknown
        """
        provider = self._providers_by_id[hardware_id]
        provider.apply_config(config)

    def save_config_as_default(self, hardware_id: str, config: Dict[str, Any]) -> None:
        """
        Save the provided configuration as the new default for the specific hardware.

        Args:
            hardware_id: Identifier of the target hardware
            config: Dictionary of parameter values keyed by spec.name

        Raises:
            KeyError: if hardware_id is unknown
        """
        provider = self._providers_by_id[hardware_id]
        provider.save_config_as_default(config)


