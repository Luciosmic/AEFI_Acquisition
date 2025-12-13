from typing import Dict, Any, List
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    BooleanParameterSchema,
    EnumParameterSchema
)

class MockHardwareAdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Mock Advanced Hardware Configurator.

    Responsibility:
    - Allow testing of "Advanced Settings" UI without real hardware.
    - Exposes generic parameters (like Speed or PID gains) for testing.
    """

    def __init__(self, hardware_id: str = "mock_advanced_hw") -> None:
        self._hardware_id = hardware_id
        self.last_config: Dict[str, Any] = {}
        # We can store state here if needed
        self.applied_params: Dict[str, Any] = {}

    @property
    def hardware_id(self) -> str:
        return self._hardware_id

    @property
    def display_name(self) -> str:
        return "Mock Advanced Hardware"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        return [
            NumberParameterSchema(
                key="pid_p",
                display_name="PID P-Gain",
                description="Proportional Gain",
                default_value=1.0,
                group="PID Control",
                min_value=0.0,
                max_value=100.0,
                unit=""
            ),
             BooleanParameterSchema(
                key="debug_mode",
                display_name="Debug Mode",
                description="Enable detailed logging",
                default_value=False,
                group="System"
            )
        ]

    def apply_config(self, config: Dict[str, Any]) -> None:
        print(f"[MockAdvancedConfig] Applying config: {config}")
        self.last_config = dict(config)
        self.applied_params.update(config)
