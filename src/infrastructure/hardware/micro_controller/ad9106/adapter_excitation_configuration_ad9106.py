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

# EXTERNAL PYTHON LIBS
from typing import Optional
from domain.models.aefi_device.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.models.aefi_device.value_objects.excitation.excitation_mode import ExcitationMode
from domain.shared.value_objects.operation_result import OperationResult
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator


# DOMAIN VALUE OBJECTS

# APPLICATION

# INFRASTRUCTURE


class AdapterExcitationConfigurationAD9106(IExcitationPort):
    """
    Infrastructure adapter for AD9106 DDS excitation hardware.
    Implements IExcitationPort interface.
    Translates domain ExcitationParameters to hardware DDS configuration.
    """
    
    # Maximum DDS gain value (hardware limit)
    MAX_DDS_GAIN = 16376
    # Next value takes over to take into accound saturation of excitation board
    # Mapping: 100% level corresponds to this hardware gain value
    # This is the maximum practical gain for excitation (not the absolute hardware max)
    MAX_EXCITATION_GAIN = 5500  # 100% level maps to 5500
    
    # Phase values from documentation (event_storming_aefi.md) and config (experimental_data_config_v3.json)
    # Phases are in 16-bit values (0-65535) representing 0-360 degrees
    # Corrected mapping (was inverted in previous code):
    # - X_DIR: DDS1=0°, DDS2=0° (In Phase)
    # - Y_DIR: DDS1=0°, DDS2=180° (Opposition) = 32768
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
        - Mode → set_dds_phase() for each channel (Gains only if active channels change)
        - Level → set_dds_gain() for active channels
        
        Optimized to minimize hardware communication:
        - Only updates parameters that have changed.
        - Strictly follows "Just change phases for mode change" rule where possible.
        
        Args:
            params: Domain excitation parameters (mode, level, frequency)
            
        Raises:
            RuntimeError: If hardware configuration fails
        """
        # Check for redundant update to avoid double communication
        if self._current_params == params:
            return

        print(f"[AD9106Adapter] apply_excitation called: mode={params.mode.name}, level={params.level.value}%, freq={params.frequency}Hz")
        
        # 1. Handle OFF mode (level=0)
        if params.level.value == 0:
            # Set DDS1 and DDS2 gains to 0, phases to 0
            for channel in [1, 2]:
                result = self._controller.set_dds_gain(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")
                result = self._controller.set_dds_phase(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} phase to 0: {result.error}")
            # Store current parameters and return
            self._current_params = params
            return

        # Determine what changed
        # If previous was None or OFF, assume everything needs update
        was_off = self._current_params is None or self._current_params.level.value == 0
        
        freq_changed = was_off or (params.frequency != self._current_params.frequency)
        level_changed = was_off or (params.level.value != self._current_params.level.value)
        mode_changed = was_off or (params.mode != self._current_params.mode)

        # 2. Set frequency (applies to all DDS channels)
        if params.frequency > 0 and freq_changed:
            result = self._controller.set_dds_frequency(params.frequency)
            if result.is_failure:
                raise RuntimeError(f"Failed to set DDS frequency: {result.error}")
        
        # 3. Map excitation mode to DDS channel configuration
        dds_config = self._map_excitation_mode_to_dds(params.mode)
        
        # 4. Set gains
        # Update gains if Level changed OR if Active Channels changed (due to mode change)
        update_gains = level_changed
        if mode_changed and not was_off:
            # Check if active channels changed
            prev_config = self._map_excitation_mode_to_dds(self._current_params.mode)
            if set(prev_config["active_channels"]) != set(dds_config["active_channels"]):
                update_gains = True
        
        if update_gains:
            # Convert level percentage (0-100) to DDS gain (0-5500)
            gain_value = int((params.level.value / 100.0) * self.MAX_EXCITATION_GAIN)
            
            # Apply gain to active channels
            active_channels = dds_config["active_channels"]
            for channel in active_channels:
                result = self._controller.set_dds_gain(channel, gain_value)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain: {result.error}")
            
            # Set inactive excitation channels (DDS1/DDS2) to 0 gain
            inactive_excitation_channels = [ch for ch in [1, 2] if ch not in active_channels]
            for channel in inactive_excitation_channels:
                result = self._controller.set_dds_gain(channel, 0)
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} gain to 0: {result.error}")
        
        # 5. Set phases
        # Update phases if Mode changed (or if we just came from OFF)
        if mode_changed:
            for channel in [1, 2]:
                phase = dds_config["phases"][channel]
                print(f"[AD9106Adapter] Setting DDS{channel} phase to {phase} (mode={params.mode.name})")
                result = self._controller.set_dds_phase(channel, phase)
                print(f"[AD9106Adapter] DDS{channel} phase set to {phase}")
                if result.is_failure:
                    raise RuntimeError(f"Failed to set DDS{channel} phase: {result.error}")
                print(f"[AD9106Adapter] DDS{channel} phase set successfully")
        
        # Store current parameters
        self._current_params = params
    
    def _map_excitation_mode_to_dds(self, mode: ExcitationMode) -> dict:
        """
        Map domain ExcitationMode to DDS channel configuration.
        
        Note: DDS3 and DDS4 are for synchronous detection and remain unchanged.
        Only DDS1 and DDS2 are used for excitation.
        
        Returns:
            Dictionary with:
            - phases: dict[channel] = phase_value
            - active_channels: list of channel numbers that should have gain
        """
        config = {
            "phases": {1: 0, 2: 0},
            "active_channels": []
        }
        
        # Map modes according to documentation (event_storming_aefi.md) and config (experimental_data_config_v3.json)
        # CORRECTED: X_DIR and Y_DIR were inverted in previous code
        if mode == ExcitationMode.Y_DIR:
            # X direction: DDS1 and DDS2 active, in phase (0°)
            # Documentation: X-Dir: DDS1=0°, DDS2=0° (In Phase)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0  # DDS1: 0°
            config["phases"][2] = 0  # DDS2: 0° (in phase)
            print(f"[AD9106Adapter] Y_DIR mode: DDS1 phase=0°, DDS2 phase=0° (in phase)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.X_DIR:
            # Y direction: DDS1 and DDS2 active, in opposition (180°)
            # Documentation: Y-Dir: DDS1=0°, DDS2=180° (Opposition)
            # Config JSON: ydir: dds1 phase_deg=180, dds2 phase_deg=0
            # Note: Config shows dds1=180, but documentation says DDS1=0°, DDS2=180°
            # Following documentation convention: DDS1=0°, DDS2=180°
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 32768  # DDS2: 180° (Opposition)
            print(f"[AD9106Adapter] X_DIR mode: DDS1 phase=0°, DDS2 phase=180° (Opposition)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_PLUS:
            # Circular rotation (clockwise): DDS1 and DDS2 with +90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=16384 (90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 16384  # DDS2: 90° (quadrature +)
            print(f"[AD9106Adapter] CIRCULAR_PLUS mode: DDS1 phase=0°, DDS2 phase=90° (16384)")
            # DDS3 and DDS4 unchanged (synchronous detection)
            
        elif mode == ExcitationMode.CIRCULAR_MINUS:
            # Circular rotation (counter-clockwise): DDS1 and DDS2 with -90° quadrature
            # Legacy: phase_dds1=0, phase_dds2=49152 (270° = -90°)
            config["active_channels"] = [1, 2]
            config["phases"][1] = 0      # DDS1: 0°
            config["phases"][2] = 49152  # DDS2: 270° (quadrature -)
            print(f"[AD9106Adapter] CIRCULAR_MINUS mode: DDS1 phase=0°, DDS2 phase=270° (49152)")
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


