from typing import List, Dict, Any
import json
import os

from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema, EnumParameterSchema, BooleanParameterSchema
)
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter

class ADS131A04AdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Advanced Configurator for ADS131A04 ADC.
    
    Responsibility:
    - Expose hardware parameters to the UI.
    - Update configuration files.
    - Apply configuration to the adapter.
    """
    
    # ADS131A04 specifications (duplicated from Adapter for now, or import if public)
    AVAILABLE_GAINS = [1, 2, 4, 8, 16, 32, 64, 128]
    AVAILABLE_OSR = [128, 256, 512, 1024, 2048, 4096, 8192, 16384]

    def __init__(self, adapter: ADS131A04Adapter):
        self._adapter = adapter

    @property
    def hardware_id(self) -> str:
        return "ads131a04"

    @property
    def display_name(self) -> str:
        return "ADS131A04 ADC"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        specs = []
        
        # Global Settings
        specs.append(NumberParameterSchema(
            key="reference_voltage",
            display_name="Reference Voltage",
            description="ADC Reference Voltage (V)",
            default_value=2.5,
            min_value=0.0,
            max_value=5.0,
            unit="V",
            group="Global"
        ))
        
        specs.append(EnumParameterSchema(
            key="oversampling_ratio",
            display_name="Oversampling Ratio (OSR)",
            description="Determines data rate and noise performance",
            default_value="32",
            choices=tuple(str(x) for x in ADS131A04AdvancedConfigurator.AVAILABLE_OSR),
            group="Global"
        ))
        
        # Channel Settings
        for ch in range(1, 7):
            specs.append(EnumParameterSchema(
                key=f"ch{ch}_gain",
                display_name=f"Channel {ch} Gain",
                description=f"PGA Gain for Channel {ch}",
                default_value="1",
                choices=tuple(str(x) for x in ADS131A04AdvancedConfigurator.AVAILABLE_GAINS),
                group=f"Channel {ch}"
            ))
            specs.append(BooleanParameterSchema(
                key=f"ch{ch}_enabled",
                display_name=f"Channel {ch} Enabled",
                description=f"Enable/Disable Channel {ch}",
                default_value=True,
                group=f"Channel {ch}"
            ))
            
        return specs

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply advanced configuration.
        
        Args:
            config: Flat dictionary of values keyed by parameter key.
        """
        # 1. Reconstruct nested JSON structure
        json_config = {
            "reference_voltage": float(config.get("reference_voltage", 2.5)),
            "clkin_divider": 2, # Fixed for now
            "iclk_divider": 2,  # Fixed for now
            "oversampling_ratio": int(config.get("oversampling_ratio", 32)),
            "channels": {}
        }
        
        for ch in range(1, 7):
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"ch{ch}_gain", 1)),
                "enabled": bool(config.get(f"ch{ch}_enabled", True))
            }
            
        # 2. Apply to adapter
        self._adapter.load_config(json_config)
        
        # 3. Persist to JSON file
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ads131a04_last_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[ADS131Configurator] Config saved to {config_path}")
        except Exception as e:
            print(f"[ADS131Configurator] Failed to save config: {e}")
