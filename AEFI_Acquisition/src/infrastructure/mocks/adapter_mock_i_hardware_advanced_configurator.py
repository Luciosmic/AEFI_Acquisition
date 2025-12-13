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
    - Exposes representative parameters matching real hardware structure:
      * Number parameters (like n_avg)
      * Boolean parameters (like high_res, negative_ref)
      * Enum parameters (like ref_voltage, oversampling_ratio)
    - Groups parameters by category (similar to ADS131A04 and MCU configurators)
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
        """
        Return mock parameter specs that represent the structure of real hardware.
        Includes examples of all parameter types used in ADS131A04 and MCU configurators.
        """
        return [
            # Number Parameter (like MCU n_avg)
            NumberParameterSchema(
                key="n_avg",
                display_name="Acquisition Averaging (n_avg)",
                description="Number of samples to average. Higher values reduce noise but increase acquisition time.",
                default_value=1,
                min_value=1,
                max_value=127,
                unit="samples",
                group="Acquisition"
            ),
            
            # Boolean Parameters (like ADS131A04 negative_ref, high_res)
            BooleanParameterSchema(
                key="high_res",
                display_name="High Resolution Mode (HRM)",
                description="High-resolution mode (better accuracy) or Low-power mode (lower power consumption).",
                default_value=True,
                group="Reference Configuration"
            ),
            BooleanParameterSchema(
                key="negative_ref",
                display_name="Negative Reference (VNCPEN)",
                description="Enable negative charge pump for unipolar power supply.",
                default_value=False,
                group="Reference Configuration"
            ),
            
            # Enum Parameters (like ADS131A04 ref_voltage, ref_selection, oversampling_ratio)
            EnumParameterSchema(
                key="ref_voltage",
                display_name="Reference Voltage Level (VREF_4V)",
                description="REFP reference voltage level when using internal reference.",
                default_value="2.442V",
                choices=("2.442V", "4.0V"),
                group="Reference Configuration"
            ),
            EnumParameterSchema(
                key="ref_selection",
                display_name="Reference Selection (INT_REFEN)",
                description="Internal or external reference voltage.",
                default_value="Internal",
                choices=("External", "Internal"),
                group="Reference Configuration"
            ),
            EnumParameterSchema(
                key="oversampling_ratio",
                display_name="Oversampling Ratio (OSR)",
                description="Determines data rate and noise performance.",
                default_value="4096",
                choices=("32", "48", "64", "96", "128", "192", "200", "256", "384", "400", "512", "768", "800", "1024", "2048", "4096"),
                group="Global"
            )
        ]

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration (mock implementation).
        
        Args:
            config: Dictionary of parameter values keyed by parameter key.
        """
        print(f"[MockAdvancedConfig] Applying config: {config}")
        self.last_config = dict(config)
        self.applied_params.update(config)
