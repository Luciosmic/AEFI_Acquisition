"""
AD9106 Excitation Configuration Adapter - Infrastructure Layer

Responsibility:
- Implement IExcitationPort interface
- Translate domain ExcitationParameters to AD9106 DDS hardware configuration
- Map excitation modes (X_DIR, Y_DIR, CIRCULAR) to DDS channel settings

Rationale:
- Separates domain logic from hardware details
- Allows domain to remain independent of specific DDS model
- Encapsulates hardware-specific mapping (phases, gains, modes)

Design:
- Hexagonal Architecture: Adapter pattern
- Translates ExcitationParameters → DDS commands
- Uses AD9106Controller for low-level hardware control
"""

from typing import Optional, List
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from domain.shared.operation_result import OperationResult
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, NumberParameterSchema, EnumParameterSchema
)
from typing import Dict, Any
import json
import os


class AD9106Adapter(IExcitationPort, IHardwareAdvancedConfigurator):
    """
    Infrastructure adapter for AD9106 DDS excitation hardware.
    Implements IExcitationPort interface.
    Translates domain ExcitationParameters to hardware DDS configuration.
    """
    
    # Maximum DDS gain value (hardware limit)
    MAX_DDS_GAIN = 16376
    
    # Mapping: 100% level corresponds to this hardware gain value
    # This is the maximum practical gain for excitation (not the absolute hardware max)
    MAX_EXCITATION_GAIN = 5500  # 100% level maps to 5500
    
    # Phase values from legacy module (EFImagingBench_ExcitationDirection_Module.py)
    # Phases are in 16-bit values (0-65535) representing 0-360 degrees
    # Legacy source of truth:
    # - ydir: phase_dds1=0, phase_dds2=0
    # - xdir: phase_dds1=0, phase_dds2=32768 (180°)
    # - circ+: phase_dds1=0, phase_dds2=16384 (90°)
    # - circ-: phase_dds1=0, phase_dds2=49152 (270°)
    
    def __init__(self, controller: Optional[AD9106Controller] = None, communicator: Optional[MCU_SerialCommunicator] = None):
        """
        Initialize AD9106 adapter.
        
        Args:
            controller: AD9106Controller instance. If None, creates one.
            communicator: MCU_SerialCommunicator (for controller creation). If None, uses singleton.
        """
        if controller:
            self._controller = controller
        else:
            comm = communicator or MCU_SerialCommunicator()
            self._controller = AD9106Controller(comm)
        
        self._current_params: Optional[ExcitationParameters] = None
    
    def apply_excitation(self, params: ExcitationParameters) -> None:
        """
        Apply excitation parameters to AD9106 hardware.
        
        Translates domain ExcitationParameters to DDS configuration:
        - Frequency → set_dds_frequency()
        - Mode → set_dds_modes() + set_dds_phase() for each channel
        - Level → set_dds_gain() for active channels
        
        Args:
            params: Domain excitation parameters (mode, level, frequency)
            
        Raises:
            RuntimeError: If hardware configuration fails
        """
        # 1. Handle OFF mode (level=0) - Legacy: gain_dds1=0, gain_dds2=0, phase_dds1=0, phase_dds2=0
        if params.level.value == 0:
            # Set DDS1 and DDS2 gains to 0, phases to 0
            for channel in [1, 2]:
                result = self._controller.set_dds_gain(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")
                result = self._controller.set_dds_phase(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} phase to 0: {result.error}")
            # Store current parameters and return (no frequency change needed for OFF)
            self._current_params = params
            return
        
        # 2. Set frequency (applies to all DDS channels)
        if params.frequency > 0:
            result = self._controller.set_dds_frequency(params.frequency)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS frequency: {result.error}")
        
        # 3. Map excitation mode to DDS channel configuration
        dds_config = self._map_excitation_mode_to_dds(params.mode)
        
        # 4. Set DDS modes (AC/DC)
        result = self._controller.set_dds_modes(
            dds1_ac=dds_config["dds1_ac"],
            dds2_ac=dds_config["dds2_ac"],
            dds3_ac=dds_config["dds3_ac"],
            dds4_ac=dds_config["dds4_ac"]
        )
        if result.is_failure:
            raise RuntimeError(f"Failed to set DDS modes: {result.error}")
        
        # 5. Set phases for excitation channels only (DDS1 and DDS2)
        # DDS3 and DDS4 remain unchanged (synchronous detection)
        for channel in [1, 2]:
            phase = dds_config["phases"][channel]
            result = self._controller.set_dds_phase(channel, phase)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS{channel} phase: {result.error}")
        
        # 6. Set gains based on excitation level
        # Convert level percentage (0-100) to DDS gain (0-5500)
        # 100% level maps to MAX_EXCITATION_GAIN (5500), not MAX_DDS_GAIN
        gain_value = int((params.level.value / 100.0) * self.MAX_EXCITATION_GAIN)
        
        # Apply gain to active channels only (DDS1 and DDS2 for excitation)
        active_channels = dds_config["active_channels"]
        for channel in active_channels:
            result = self._controller.set_dds_gain(channel, gain_value)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS{channel} gain: {result.error}")
        
        # Set inactive excitation channels (DDS1/DDS2) to 0 gain
        # DDS3 and DDS4 remain unchanged (synchronous detection)
        inactive_excitation_channels = [ch for ch in [1, 2] if ch not in active_channels]
        for channel in inactive_excitation_channels:
            result = self._controller.set_dds_gain(channel, 0)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")
        
        # Store current parameters
        self._current_params = params
    
    def _map_excitation_mode_to_dds(self, mode: ExcitationMode) -> dict:
        """
        Map domain ExcitationMode to DDS channel configuration.
        
        Note: DDS3 and DDS4 are for synchronous detection and remain unchanged.
        Only DDS1 and DDS2 are used for excitation.
        
        Returns:
            Dictionary with:
            - dds1_ac, dds2_ac, dds3_ac, dds4_ac: bool (AC/DC mode)
            - phases: dict[channel] = phase_value
            - active_channels: list of channel numbers that should have gain
        """
        config = {
            "dds1_ac": True,
            "dds2_ac": True,
            "dds3_ac": True,  # Keep AC mode (for detection)
            "dds4_ac": True,  # Keep AC mode (for detection)
            "phases": {1: 0, 2: 0, 3: 16384, 4: 0},  # Default phases (DDS3=90° for detection)
            "active_channels": []
        }
        
        # Map modes according to legacy module (EFImagingBench_ExcitationDirection_Module.py)
        if mode == ExcitationMode.X_DIR:
            # X direction: DDS1 and DDS2 active, in opposition (180°)
            # Legacy: phase_dds1=0, phase_dds2=32768 (180°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 32768  # DDS2: 180° (opposition)
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.Y_DIR:
            # Y direction: DDS1 and DDS2 active, in phase (0°)
            # Legacy: phase_dds1=0, phase_dds2=0
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0  # DDS1: 0°
            config["phases"][2] = 0  # DDS2: 0° (in phase)
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_PLUS:
            # Circular rotation (clockwise): DDS1 and DDS2 with +90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=16384 (90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 16384  # DDS2: 90° (quadrature +)
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_MINUS:
            # Circular rotation (counter-clockwise): DDS1 and DDS2 with -90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=49152 (270° = -90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 49152  # DDS2: 270° (quadrature -)
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CUSTOM:
            # Custom mode: use current hardware state (no change to phases/modes)
            # Only frequency and level will be updated
            memory_state = self._controller.get_memory_state()
            # Determine active channels from current gain values (only DDS1/DDS2 for excitation)
            for channel in [1, 2]:
                if memory_state["DDS"]["Gain"][channel] > 0:
                    config["active_channels"].append(channel)
                config["phases"][channel] = memory_state["DDS"]["Phase"][channel]
            # DDS3 and DDS4 phases remain unchanged
        
        return config
    
    def get_controller(self) -> AD9106Controller:
        """Get the underlying AD9106Controller (for lifecycle initialization)."""
        return self._controller

    # ==========================================================================
    # IHardwareAdvancedConfigurator Implementation
    # ==========================================================================

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
            min_value=0.0,
            max_value=8000000.0, # 8 MHz
            unit="Hz",
            group="Global"
        ))
        
        # Modes
        modes = ("AC+AC", "AC+DC", "DC+AC", "DC+DC")
        specs.append(EnumParameterSchema(
            key="mode_dds1_dds2",
            display_name="Mode DDS1+DDS2",
            description="Combined mode for DDS1 and DDS2",
            default_value="AC+AC",
            choices=modes,
            group="Global"
        ))
        specs.append(EnumParameterSchema(
            key="mode_dds3_dds4",
            display_name="Mode DDS3+DDS4",
            description="Combined mode for DDS3 and DDS4",
            default_value="AC+AC",
            choices=modes,
            group="Global"
        ))
        
        # Channel Settings
        for ch in range(1, 5):
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
                
            # Modes
            # Note: Controller has set_dds_modes(bools) or set_dds_channel_mode(str).
            # But here we have combined modes strings like "AC+AC".
            # We need to parse them.
            # Or better, update the controller to handle this? 
            # For now, I'll parse here.
            mode_map = {"AC": True, "DC": False}
            
            if "mode_dds1_dds2" in config:
                parts = config["mode_dds1_dds2"].split('+')
                if len(parts) == 2:
                    self._controller.set_dds_channel_mode(1, parts[0])
                    self._controller.set_dds_channel_mode(2, parts[1])
                    
            if "mode_dds3_dds4" in config:
                parts = config["mode_dds3_dds4"].split('+')
                if len(parts) == 2:
                    self._controller.set_dds_channel_mode(3, parts[0])
                    self._controller.set_dds_channel_mode(4, parts[1])

            # Channels
            for ch in range(1, 5):
                if f"ch{ch}_gain" in config:
                    self._controller.set_dds_gain(ch, int(config[f"ch{ch}_gain"]))
                if f"ch{ch}_phase" in config:
                    self._controller.set_dds_phase(ch, int(config[f"ch{ch}_phase"]))
                if f"ch{ch}_offset" in config:
                    self._controller.set_dds_offset(ch, int(config[f"ch{ch}_offset"]))
                    
        except Exception as e:
            print(f"[AD9106Adapter] Failed to apply config to hardware: {e}")
            # Don't raise, try to save JSON anyway? Or raise?
            # If hardware fails, maybe we shouldn't save invalid config.
            raise e

        # 2. Reconstruct JSON structure and Save
        json_config = {
            "frequency_hz": float(config.get("frequency_hz", 1000)),
            "mode_dds1_dds2": config.get("mode_dds1_dds2", "AC+AC"),
            "mode_dds3_dds4": config.get("mode_dds3_dds4", "AC+AC"),
            "channels": {},
            "dacs": {} # Not exposed in advanced config yet, but needed for JSON structure
        }
        
        for ch in range(1, 5):
            json_config["channels"][str(ch)] = {
                "gain": int(config.get(f"ch{ch}_gain", 0)),
                "phase": int(config.get(f"ch{ch}_phase", 0)),
                "offset": int(config.get(f"ch{ch}_offset", 0))
            }
            # Preserve DAC offsets if they were there? 
            # For now, just initialize to 0 as per default structure.
            json_config["dacs"][str(ch)] = {"offset": 0}
            
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ad9106_last_config.json")
            with open(config_path, 'w') as f:
                json.dump(json_config, f, indent=4)
            print(f"[AD9106Adapter] Config saved to {config_path}")
        except Exception as e:
            print(f"[AD9106Adapter] Failed to save config: {e}")

