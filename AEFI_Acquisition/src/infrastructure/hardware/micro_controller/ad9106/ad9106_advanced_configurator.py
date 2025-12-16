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
from dataclasses import replace

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
            display_name="Frequency",
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
                display_name=f"DDS {ch} Gain",
                description=f"Digital Gain for DDS {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=16376.0,
                group=f"DDS {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_phase",
                display_name=f"DDS {ch} Phase",
                description=f"Phase Offset for DDS {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"DDS {ch}"
            ))
            specs.append(NumberParameterSchema(
                key=f"ch{ch}_offset",
                display_name=f"DDS {ch} Offset",
                description=f"DC Offset for DDS {ch}",
                default_value=0.0,
                min_value=0.0,
                max_value=65535.0,
                group=f"DDS {ch}"
            ))
            


        # Load default config if exists
        updated_specs = []
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ad9106_default_config.json")
            default_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    default_config = json.load(f)
            
            for spec in specs:
                new_default = spec.default_value
                
                # Global
                if spec.key == "frequency_hz" and "frequency_hz" in default_config:
                    new_default = default_config["frequency_hz"]
                
                # Channels
                if spec.key.startswith("ch"):
                    # Parse key: ch{ch}_{param}
                    parts = spec.key.split("_")
                    if len(parts) >= 2:
                        ch_str = parts[0][2:] # "1" from "ch1"
                        param = parts[1] # "gain", "phase", "offset"
                        
                        if "channels" in default_config and ch_str in default_config["channels"]:
                            ch_config = default_config["channels"][ch_str]
                            if param in ch_config:
                                new_default = float(ch_config[param])
                
                if new_default != spec.default_value:
                    updated_specs.append(replace(spec, default_value=new_default))
                else:
                    updated_specs.append(spec)
                                    
        except Exception as e:
            print(f"[AD9106Configurator] Failed to load default config: {e}")
            return specs
            
        return updated_specs

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
                if f"dds{ch}_gain" in config:
                    self._controller.set_dds_gain(ch, int(config[f"dds{ch}_gain"]))
                if f"dds{ch}_phase" in config:
                    self._controller.set_dds_phase(ch, int(config[f"dds{ch}_phase"]))
                if f"dds{ch}_offset" in config:
                    self._controller.set_dds_offset(ch, int(config[f"dds{ch}_offset"]))
                    
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

    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save configuration as default.
        """
        # Reconstruct JSON structure
        json_config = {
            "frequency_hz": float(config.get("frequency_hz", 1000)),
            "channels": {},
            "dacs": {}
        }
        
        for ch in range(1, 3):
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"dds{ch}_gain", 0)),
                "phase": int(config.get(f"dds{ch}_phase", 0)),
                "offset": int(config.get(f"dds{ch}_offset", 0))
            }
            json_config["dacs"][str(ch)] = {"offset": 0}
            
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ad9106_default_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[AD9106AdvancedConfigurator] Default config saved to {config_path}")
        except Exception as e:
            print(f"[AD9106AdvancedConfigurator] Failed to save default config: {e}")
            raise e
