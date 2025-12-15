"""
Arcus Performax 4EX - Advanced Configuration Module

Responsibility:
- Centralize ALL Arcus advanced configuration (speed, acceleration, homing)
- Provide unified view of all configurable parameters
- Isolate Arcus-specific configuration logic

Rationale:
- Single source of truth for Arcus configuration
- Easier to maintain and extend
- Clear separation from motion control port
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    BooleanParameterSchema,
)
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import (
    IHardwareAdvancedConfigurator,
)
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import (
    ArcusPerformax4EXController,
)


class ArcusAdvancedConfigurationSpecs:
    """
    Centralized definition of all Arcus configurable parameters.
    
    Responsibility:
    - Define all parameter specifications in one place
    - Provide single source of truth for Arcus configuration UI
    """
    
    @staticmethod
    def get_all_specs() -> List[HardwareAdvancedParameterSchema]:
        """
        Get all Arcus configurable parameters.
        
        Parameters are aligned with the low-level LS/HS/ACC/DEC registers:
        - LS* : low speed (Hz)
        - HS* : high speed (Hz)
        - ACC* : acceleration time (ms)
        - DEC* : deceleration time (ms)
        """
        return [
            # === X Axis Speed Parameters (LSX / HSX / ACCX / DECX) ===
            NumberParameterSchema(
                key="x_ls",
                display_name="X Low Speed (LSX)",
                description="X axis low speed (LSX, in Hz)",
                default_value=10,
                min_value=1,
                max_value=5000,  # TODO: refine from Arcus datasheet
                unit="Hz",
                group="X Axis Speed",
            ),
            NumberParameterSchema(
                key="x_hs",
                display_name="X High Speed (HSX)",
                description="X axis high speed (HSX, in Hz). Default: 1500 Hz (~6.54 cm/s)",
                default_value=6000,
                min_value=10,
                max_value=10000,  # TODO: refine from Arcus datasheet
                unit="Hz",
                group="X Axis Speed",
            ),
            NumberParameterSchema(
                key="x_acc",
                display_name="X Acceleration (ACCX)",
                description="X axis acceleration time (ACCX, in ms)",
                default_value=1000,
                min_value=10,
                max_value=10000,
                unit="ms",
                group="X Axis Speed",
            ),
            NumberParameterSchema(
                key="x_dec",
                display_name="X Deceleration (DECX)",
                description="X axis deceleration time (DECX, in ms). Higher value = softer stop. Default: 600ms",
                default_value=1000,
                min_value=10,
                max_value=10000,
                unit="ms",
                group="X Axis Speed",
            ),

            # === Y Axis Speed Parameters (LSY / HSY / ACCY / DECY) ===
            NumberParameterSchema(
                key="y_ls",
                display_name="Y Low Speed (LSY)",
                description="Y axis low speed (LSY, in Hz)",
                default_value=10,
                min_value=1,
                max_value=5000,  # TODO: refine from Arcus datasheet
                unit="Hz",
                group="Y Axis Speed",
            ),
            NumberParameterSchema(
                key="y_hs",
                display_name="Y High Speed (HSY)",
                description="Y axis high speed (HSY, in Hz). Default: 1500 Hz (~6.54 cm/s)",
                default_value=6000,
                min_value=10,
                max_value=10000,  # TODO: refine from Arcus datasheet
                unit="Hz",
                group="Y Axis Speed",
            ),
            NumberParameterSchema(
                key="y_acc",
                display_name="Y Acceleration (ACCY)",
                description="Y axis acceleration time (ACCY, in ms)",
                default_value=1000,
                min_value=10,
                max_value=10000,
                unit="ms",
                group="Y Axis Speed",
            ),
            NumberParameterSchema(
                key="y_dec",
                display_name="Y Deceleration (DECY)",
                description="Y axis deceleration time (DECY, in ms). Higher value = softer stop. Default: 600ms",
                default_value=1000,
                min_value=10,
                max_value=10000,
                unit="ms",
                group="Y Axis Speed",
            ),

            # === Homing Action ===
            # Represented as BooleanParameterSchema (checked = trigger homing)
            BooleanParameterSchema(
                key="home_both_axes",
                display_name="Home X and Y",
                description="Home both X and Y axes (negative direction, home inputs)",
                default_value=False,
                group="Homing",
            ),
        ]


class ArcusAdvancedConfigurationApplier:
    """
    Applies Arcus configuration to hardware controller.
    
    Responsibility:
    - Bridge high-level configuration dict to low-level controller API
    - Handle parameter resolution (specific > generic)
    - Apply speed, acceleration, deceleration, and homing
    """
    
    def __init__(self, controller: ArcusPerformax4EXController):
        self._controller = controller
    
    def apply(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration to Arcus hardware.
        
        Resolves generic (e.g. 'hs') and specific (e.g. 'x_hs') parameters
        and applies them using the controller's set_axis_params method.
        """
        if not config:
            return

        # Helper to resolve parameter value (specific > generic > None)
        def _resolve(param_name: str, axis_prefix: str) -> Optional[int]:
            specific_key = f"{axis_prefix}_{param_name}"
            if specific_key in config and config[specific_key] is not None:
                return int(config[specific_key])
            if param_name in config and config[param_name] is not None:
                return int(config[param_name])
            return None

        # Apply for X Axis
        x_params = {
            "ls": _resolve("ls", "x"),
            "hs": _resolve("hs", "x"),
            "acc": _resolve("acc", "x"),
            "dec": _resolve("dec", "x"),
        }
        # Only call if at least one param is set
        if any(v is not None for v in x_params.values()):
            self._controller.set_axis_params("x", **x_params)

        # Apply for Y Axis
        y_params = {
            "ls": _resolve("ls", "y"),
            "hs": _resolve("hs", "y"),
            "acc": _resolve("acc", "y"),
            "dec": _resolve("dec", "y"),
        }
        if any(v is not None for v in y_params.values()):
            self._controller.set_axis_params("y", **y_params)

        # Homing via controller if requested
        if config.get("home_both_axes"):
            self._controller.home_both(blocking=True)


class ArcusPerformax4EXAdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Hardware configuration provider for Arcus Performax 4EX motor controller.

    Responsibility:
    - Describe axis speed and homing parameters in a UI-agnostic way
    - Provide specs that application/UI can use to build configuration screens
    - Implement IHardwareAdvancedConfigurator interface

    Rationale:
    - Single entry point for Arcus advanced configuration
    - Uses centralized specs and applier for maintainability
    """

    def __init__(self, controller: Optional[ArcusPerformax4EXController] = None) -> None:
        """
        Optionally inject a controller instance.

        If no controller is provided, apply_config will create a short-lived
        controller to apply settings.
        """
        self._controller = controller

    @property
    def hardware_id(self) -> str:
        return "arcus_performax_4ex_advanced"

    @property
    def display_name(self) -> str:
        return "Arcus Performax 4EX (Advanced)"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        """
        Get actionable parameter specifications for Arcus Performax 4EX.
        
        Delegates to centralized specs definition.
        """
        return ArcusAdvancedConfigurationSpecs.get_all_specs()

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration to Arcus hardware.
        
        Uses centralized applier for consistency.
        """
        # Use injected controller if available, otherwise create a short-lived one
        if self._controller is not None:
            controller = self._controller
            owns_controller = False
        else:
            dll_path = Path(__file__).parent / "DLL64"
            controller = ArcusPerformax4EXController(dll_path=str(dll_path))
            owns_controller = True

        try:
            if owns_controller:
                connected = controller.connect()
                if not connected:
                    raise RuntimeError("Failed to connect ArcusPerformax4EXController")

            applier = ArcusAdvancedConfigurationApplier(controller)
            applier.apply(config)
        finally:
            if owns_controller:
                controller.disconnect()

