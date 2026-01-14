from typing import List, Dict, Any
import json
import os
from dataclasses import replace

from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema
)
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator

class MCUAdvancedConfigurator(IHardwareAdvancedConfigurator):
    """
    Advanced Configurator for MCU (MicroController Unit).
    
    Responsibility:
    - Expose MCU parameters to the UI.
    - Update configuration files.
    - Store n_avg parameter for acquisition averaging.
    """
    
    # MCU acquisition averaging limits (from legacy code)
    NAVG_MIN = 1
    NAVG_MAX = 127

    def __init__(self, serial_communicator: MCU_SerialCommunicator):
        """
        Args:
            serial_communicator: MCU serial communicator instance
        """
        self._serial = serial_communicator

    @property
    def hardware_id(self) -> str:
        return "mcu"

    @property
    def display_name(self) -> str:
        return "MCU (MicroController Unit)"

    @staticmethod
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        """
        Get parameter specifications for MCU configuration.
        
        Returns:
            List of HardwareAdvancedParameterSchema
        """
        specs = []
        
        # Acquisition Averaging
        specs.append(NumberParameterSchema(
            key="n_avg",
            display_name="Acquisition Averaging (n_avg)",
            description="Number of samples to average on MCU before returning data. Higher values reduce noise but increase acquisition time. Range: 1-127",
            default_value=1,
            min_value=1,
            max_value=127,
            unit="samples",
            group="Acquisition"
        ))
        


        # Load default config if exists
        updated_specs = []
        try:
            config_path = os.path.join(os.path.dirname(__file__), "mcu_default_config.json")
            default_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    default_config = json.load(f)
            
            for spec in specs:
                if spec.key == "n_avg" and "n_avg" in default_config:
                    updated_specs.append(replace(spec, default_value=default_config["n_avg"]))
                else:
                    updated_specs.append(spec)
                        
        except Exception as e:
            print(f"[MCUConfigurator] Failed to load default config: {e}")
            return specs
            
        return updated_specs

    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply advanced configuration.
        
        Args:
            config: Flat dictionary of values keyed by parameter key.
        """
        # 1. Validate and extract n_avg
        n_avg = int(config.get("n_avg", 1))
        
        if not (self.NAVG_MIN <= n_avg <= self.NAVG_MAX):
            raise ValueError(f"n_avg must be between {self.NAVG_MIN} and {self.NAVG_MAX}, got {n_avg}")
        
        # 2. Reconstruct JSON structure
        json_config = {
            "n_avg": n_avg
        }
        
        # 3. Persist to JSON file
        try:
            config_path = os.path.join(os.path.dirname(__file__), "mcu_last_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[MCUConfigurator] Config saved to {config_path}: n_avg={n_avg}")
        except Exception as e:
            print(f"[MCUConfigurator] Failed to save config: {e}")
            raise

    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        """
        Save configuration as default.
        """
        n_avg = int(config.get("n_avg", 1))
        
        if not (self.NAVG_MIN <= n_avg <= self.NAVG_MAX):
            raise ValueError(f"n_avg must be between {self.NAVG_MIN} and {self.NAVG_MAX}, got {n_avg}")
        
        json_config = {
            "n_avg": n_avg
        }
        
        try:
            config_path = os.path.join(os.path.dirname(__file__), "mcu_default_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[MCUConfigurator] Default config saved to {config_path}: n_avg={n_avg}")
        except Exception as e:
            print(f"[MCUConfigurator] Failed to save default config: {e}")
            raise e
    
    def get_n_avg(self) -> int:
        """
        Get current n_avg value from saved configuration.
        
        Returns:
            Current n_avg value (default: 1)
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), "mcu_last_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    return int(saved_config.get("n_avg", 1))
        except Exception as e:
            print(f"[MCUConfigurator] Failed to read saved config: {e}")
        
        # Fallback to default
        return 1



