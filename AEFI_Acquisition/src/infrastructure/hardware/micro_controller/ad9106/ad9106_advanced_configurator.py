"""
AD9106 Advanced Configurator - Infrastructure Layer

Responsibility:
- Implement IHardwareAdvancedConfigurator interface
- Expose low-level AD9106 configuration (Gains, Phases, Offsets) for manual tuning
- Save/Load last configuration

Rationale:
- Extracted from AD9106Adapter to separate concerns (SRP).
- The Adapter focuses on Domain -> Hardware translation (Excitation).
- The Configurator focuses on User -> Hardware tuning (Advanced Config).
"""

from typing import List, Dict, Any
import json
import os

from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema
)
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller


class AD9106AdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Advanced Configurator for AD9106 DDS hardware.
    Allows manual tuning of registers via the UI.
    """

    def __init__(self, controller: AD9106Controller):
        """
        Initialize configurator with shared controller.
        
        Args:
            controller: AD9106Controller instance (shared with Adapter).
        """
        self._controller = controller

    @property
    def hardware_id(self) -> str:
        return "ad9106_dds"

    @property
    def display_name(self) -> str:
        return "AD9106 DDS"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        specs = []
        
        # Global Settings
        specs.append(NumberParameterSchema(
            key="frequency_hz",
            display_name="Frequency (Hz)",
            description="DDS Output Frequency",
            default_value=1000.0,
            min_value=0.1,
            max_value=8000000.0, # 8 MHz
            unit="Hz",
            group="Global"
        ))
        
        # Channel Settings (Restricted to DDS1 and DDS2 as per requirements)
        for ch in range(1, 3):
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_gain",
                display_name=f"Channel {ch} Gain",
                description=f"Digital Gain for Channel {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=16376.0,
                group=f"Channel {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_phase",
                display_name=f"Channel {ch} Phase",
                description=f"Phase Offset for Channel {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"Channel {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_offset",
                display_name=f"Channel {ch} Offset",
                description=f"DC Offset for Channel {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"Channel {ch}"
            ))
            
        return specs

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply advanced configuration.
        
        Args:
            config: Flat dictionary of values keyed by parameter key.
        """
        # 1. Apply to Hardware via Controller
        try:
            # Frequency
            if "frequency_hz" in config:
                self._controller.set_dds_frequency(float(config["frequency_hz"]))
                

            # Channels (Restricted to DDS1 and DDS2)
            for ch in range(1, 3):
                if f"ch{ch}_gain" in config:
                    self._controller.set_dds_gain(ch, int(config[f"ch{ch}_gain"]))
                if f"ch{ch}_phase" in config:
                    self._controller.set_dds_phase(ch, int(config[f"ch{ch}_phase"]))
                if f"ch{ch}_offset" in config:
                    self._controller.set_dds_offset(ch, int(config[f"ch{ch}_offset"]))
                    
        except Exception as e:
            print(f"[AD9106AdvancedConfigurator] Failed to apply config to hardware: {e}")
            raise e

        # 2. Reconstruct JSON structure and Save
        json_config = {
            "frequency_hz": float(config.get("frequency_hz", 1000)),

            "channels": {},
            "dacs": {} # Not exposed in advanced config yet, but needed for JSON structure
        }
        
        for ch in range(1, 3):
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"ch{ch}_gain", 0)),
                "phase": int(config.get(f"ch{ch}_phase", 0)),
                "offset": int(config.get(f"ch{ch}_offset", 0))
            }
            # Preserve DAC offsets if they were there? 
            # For now, just initialize to 0 as per default structure.
            json_config["dacs"][str(ch)] = {"offset": 0}
            
        try:
            # Save to the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), "ad9106_last_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[AD9106AdvancedConfigurator] Config saved to {config_path}")
        except Exception as e:
            print(f"[AD9106AdvancedConfigurator] Failed to save config: {e}")
