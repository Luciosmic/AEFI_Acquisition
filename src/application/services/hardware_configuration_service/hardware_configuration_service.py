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

import logging
from typing import Any, Dict, List, Optional

from application.shared.exclusive_control.exclusive_control import ExclusiveControl
from domain.shared_kernel.events.hardware_configuration_control_changed.hardware_configuration_control_changed import (
    HardwareConfigurationControlChanged,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema
from .i_api_hardware_configuration_service import IApiHardwareConfigurationService
from .ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

HARDWARE_CONFIGURATION_CONTROL_CHANGED_TOPIC = "hardwareconfigurationcontrolchanged"

logger = logging.getLogger(__name__)


class HardwareConfigurationService(IApiHardwareConfigurationService):
    """
    Application-level service for hardware configuration discovery.
    """

    def __init__(
        self, providers: List[IHardwareAdvancedConfigurator], event_bus: Optional[IDomainEventBus] = None
    ) -> None:
        """
        Initialize the service with a list of advanced configurators (injected from composition root).

        Args:
            providers: Concrete implementations of IHardwareAdvancedConfigurator
            event_bus: where a change of owner of a hardware's configuration is
                published (None: not published — tests that do not watch it)
        """
        self._providers_by_id: Dict[str, IHardwareAdvancedConfigurator] = {
            provider.hardware_id: provider for provider in providers
        }
        # One single owner per hardware (e.g. the throughput characterization
        # holds "mcu" and "ads131a04"): while held, Apply / Save as Default /
        # Reset to Default from this service are refused.
        self._controls: Dict[str, ExclusiveControl] = {
            hardware_id: ExclusiveControl(
                f"configuration {hardware_id}",
                lambda controller, hardware_id=hardware_id: event_bus is not None and event_bus.publish(
                    HARDWARE_CONFIGURATION_CONTROL_CHANGED_TOPIC,
                    HardwareConfigurationControlChanged(hardware_id=hardware_id, controller=controller),
                ),
            )
            for hardware_id in self._providers_by_id
        }

    # -- control (single owner per hardware) --------------------------------------

    def take_control(self, hardware_id: str, controller: str) -> OperationResult[None, str]:
        """Raises KeyError if hardware_id is unknown."""
        logger.info(
            "HardwareConfigurationService: Command take_control hardware_id=%s controller=%s", hardware_id, controller
        )
        return self._controls[hardware_id].take(controller)

    def release_control(self, hardware_id: str, controller: str) -> None:
        if hardware_id in self._controls:
            self._controls[hardware_id].release(controller)

    def get_controller(self, hardware_id: str) -> Optional[str]:
        control = self._controls.get(hardware_id)
        return control.controller if control is not None else None

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

    def apply_config(self, hardware_id: str, config: Dict[str, Any]) -> OperationResult[None, str]:
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
        logger.info("HardwareConfigurationService: apply_config hardware_id=%s", hardware_id)
        provider = self._providers_by_id[hardware_id]
        refusal = self._controls[hardware_id].refusal(None, "apply_config")
        if refusal is not None:
            return OperationResult.fail(refusal)
        provider.apply_config(config)
        return OperationResult.ok(None)

    def save_config_as_default(self, hardware_id: str, config: Dict[str, Any]) -> OperationResult[None, str]:
        """
        Save the provided configuration as the new default for the specific hardware.

        Args:
            hardware_id: Identifier of the target hardware
            config: Dictionary of parameter values keyed by spec.name

        Raises:
            KeyError: if hardware_id is unknown
        """
        logger.info("HardwareConfigurationService: save_config_as_default hardware_id=%s", hardware_id)
        provider = self._providers_by_id[hardware_id]
        refusal = self._controls[hardware_id].refusal(None, "save_config_as_default")
        if refusal is not None:
            return OperationResult.fail(refusal)
        provider.save_config_as_default(config)
        return OperationResult.ok(None)

    def reset_to_default(self, hardware_id: str) -> OperationResult[None, str]:
        """
        Discard the current applied/last state for a hardware and re-apply
        its saved default configuration.

        Args:
            hardware_id: Identifier of the target hardware

        Raises:
            KeyError: if hardware_id is unknown
        """
        logger.info("HardwareConfigurationService: reset_to_default hardware_id=%s", hardware_id)
        provider = self._providers_by_id[hardware_id]
        refusal = self._controls[hardware_id].refusal(None, "reset_to_default")
        if refusal is not None:
            return OperationResult.fail(refusal)
        provider.reset_to_default()
        return OperationResult.ok(None)


