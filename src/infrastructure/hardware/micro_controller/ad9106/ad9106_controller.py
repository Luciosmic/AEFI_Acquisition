"""
AD9106 Controller - Infrastructure Layer

Responsibility:
- Low-level control of AD9106 DDS (Direct Digital Synthesizer) hardware
- Manage DDS configuration (frequency, modes, gains, phases, offsets)
- Organize methods using QCS pattern (Setup, Commands, Queries)

Rationale:
- Encapsulates AD9106-specific hardware details
- Provides clean interface for adapters
- Manages hardware state (memory_state) for consistency

Design (QCS):
- SETUP: connection lifecycle (connect, disconnect, init_default_config)
- COMMAND: configuration commands (set_dds_frequency, set_dds_gain, etc.)
- QUERY: state queries (get_memory_state)
"""

from typing import Dict, Optional, Tuple
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from domain.shared.operation_result import OperationResult


class AD9106Controller:
    """
    Controller for AD9106 DDS hardware.
    
    QCS Organization:
    - SETUP: connect, disconnect, init_default_config
    - COMMAND: set_dds_* methods
    - QUERY: get_memory_state
    """
    
    # Hardware register addresses (AD9106 datasheet)
    DDS_ADDRESSES = {
        "Frequency": [62, 63],   # 62: MSB, 63: LSB
        # Mode registers are shared between pairs of channels:
        # - Channels 1 & 2 share register 39
        # - Channels 3 & 4 share register 38
        "Mode": {1: 39, 2: 39, 3: 38, 4: 38},
        "Gain": {1: 53, 2: 52, 3: 51, 4: 50},  # Gain DDS1-4
        "Offset": {1: 37, 2: 36, 3: 35, 4: 34},  # Offset DDS1-4 (DAC1-4DOF: 37=DAC1, 36=DAC2, 35=DAC3, 34=DAC4)
        "Phase": {1: 67, 2: 66, 3: 65, 4: 64},    # Phase DDS1-4
        "Const": {1: 49, 2: 48, 3: 47, 4: 46}     # Constante DDS1-4
    }
    
    # Clock frequency for frequency calculation (16 MHz)
    DDS_CLOCK_FREQ_HZ = 16_000_000
    
    def __init__(self, communicator: Optional[MCU_SerialCommunicator] = None):
        """
        Initialize AD9106 controller.
        
        Args:
            communicator: MCU serial communicator (singleton). If None, gets instance.
        """
        self._communicator = communicator or MCU_SerialCommunicator()
        self._memory_state: Dict = {
            "DDS": {
                "Frequence": 1000,  # Hz
                "Mode": {1: "AC", 2: "AC", 3: "AC", 4: "AC"},
                "Gain": {1: 0, 2: 0, 3: 10000, 4: 10000},
                "Offset": {1: 0, 2: 0, 3: 0, 4: 0},
                "Phase": {1: 0, 2: 32768, 3: 16384, 4: 0},
                "Const": {1: 0, 2: 0, 3: 0, 4: 0}
            }
        }
        self._freq_msb: Optional[int] = None
        self._freq_lsb: Optional[int] = None
    
    # ==========================================================================
    # SETUP
    # ==========================================================================
    
    def init_default_config(self) -> OperationResult[None, str]:
        """
        SETUP: Initialize AD9106 with default configuration.
        
        Default configuration:
        - Modes DDS en AC+AC
        - Offsets numériques DAC à 0
        - Gains DDS à 10000 (DDS3/4) ou 0 (DDS1/2)
        - Frequency: 1000 Hz
        """
        try:
            # Default configuration sequence (from legacy init_default_config)
            params_default = [
                (63, 12583),  # DDS: Frequence_DDS (LSB) - corresponds to ~1000 Hz
                (62, 8),      # DDS: Frequence_DDS (MSB)
                (38, 12593),  # DDS: Mode DDS3+DDS4 (AC+AC)
                (39, 12593),  # DDS: Mode DDS1+DDS2 (AC+AC)
                (34, 0),      # DAC4DOF (Offset numérique DAC4)
                (35, 0),      # DAC3DOF (Offset numérique DAC3)
                (36, 0),      # DAC2DOF (Offset numérique DAC2)
                (37, 0),      # DAC1DOF (Offset numérique DAC1)
                (49, 0),      # DDS: Const_1
                (53, 0),      # DDS: Gain_1 (no excitation on startup)
                (67, 0),      # DDS: Phase_1
                (48, 0),      # DDS: Const_2
                (52, 0),      # DDS: Gain_2 (no excitation on startup)
                (66, 32768),  # DDS: Phase_2
                (47, 0),      # DDS: Const_3
                (51, 10000),  # DDS: Gain_3
                (65, 16384),  # DDS: Phase_3
                (46, 0),      # DDS: Const_4
                (50, 10000),  # DDS: Gain_4
                (64, 0),      # DDS: Phase_4
            ]
            
            for address, value in params_default:
                # Select register
                success, response = self._communicator.send_command(f"a{address}")
                if not success:
                    return OperationResult.fail(f"Failed to select address {address}: {response}")
                
                # Write data
                success, response = self._communicator.send_command(f"d{value}")
                if not success:
                    return OperationResult.fail(f"Failed to write value {value} to address {address}: {response}")
                
                # Update memory state
                self._update_memory_from_address(address, value)
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Initialization failed: {str(e)}")
    
    # ==========================================================================
    # COMMANDS
    # ==========================================================================
    
    def set_dds_frequency(self, freq_hz: float) -> OperationResult[None, str]:
        """
        COMMAND: Configure DDS frequency for all channels.
        
        Args:
            freq_hz: Frequency in Hz (0 to ~8 MHz)
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # Convert frequency to uint32
            success, result = self._freq_to_uint32(freq_hz)
            if not success:
                return OperationResult.fail(result)
            valeur_32bits = result
            
            # Decompose into MSB and LSB
            success, result = self._decomposer_uint32(valeur_32bits)
            if not success:
                return OperationResult.fail(result)
            partie_haute, partie_basse = result
            
            # Send MSB (address 62)
            success, response = self._communicator.send_command(f"a{self.DDS_ADDRESSES['Frequency'][0]}")
            if not success:
                return OperationResult.fail(f"Failed to select MSB address: {response}")
            
            success, response = self._communicator.send_command(f"d{partie_haute}")
            if not success:
                return OperationResult.fail(f"Failed to write MSB value: {response}")
            
            # Send LSB (address 63)
            success, response = self._communicator.send_command(f"a{self.DDS_ADDRESSES['Frequency'][1]}")
            if not success:
                return OperationResult.fail(f"Failed to select LSB address: {response}")
            
            success, response = self._communicator.send_command(f"d{partie_basse}")
            if not success:
                return OperationResult.fail(f"Failed to write LSB value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Frequence"] = freq_hz
            self._freq_msb = partie_haute
            self._freq_lsb = partie_basse
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set frequency failed: {str(e)}")
    
    def set_dds_modes(self, dds1_ac: bool, dds2_ac: bool, dds3_ac: bool, dds4_ac: bool) -> OperationResult[None, str]:
        """
        COMMAND: Configure modes (AC/DC) for all four DDS channels.
        
        Args:
            dds1_ac: True for AC, False for DC on DDS1
            dds2_ac: True for AC, False for DC on DDS2
            dds3_ac: True for AC, False for DC on DDS3
            dds4_ac: True for AC, False for DC on DDS4
            
        Returns:
            OperationResult indicating success or failure
        """
        try:
            # --- Configure DDS1 & DDS2 (Register 39) ---
            # Register 39 controls both DDS1 and DDS2.
            # - Lower 8 bits (0-7): Controls DDS1
            # - Upper 8 bits (8-15): Controls DDS2
            
            # 1. Determine value for each channel (AC=0x31, DC=0x01)
            MODE_AC = 0x31
            MODE_DC = 0x01
            
            val_1 = MODE_AC if dds1_ac else MODE_DC
            val_2 = MODE_AC if dds2_ac else MODE_DC
            
            # 2. Combine values into a single 16-bit integer
            # val_1 is placed in the lower byte (no shift)
            # val_2 is shifted 8 bits to the left to occupy the upper byte
            # |  DDS2 (8 bits)  |  DDS1 (8 bits)  |
            valeur_dds12 = val_1 | (val_2 << 8)
            
            # 3. Send command to Register 39
            success, response = self._communicator.send_command(f"a{self.DDS_ADDRESSES['Mode'][1]}")
            if not success:
                return OperationResult.fail(f"Failed to select Mode register for DDS1/2: {response}")
            
            success, response = self._communicator.send_command(f"d{valeur_dds12}")
            if not success:
                return OperationResult.fail(f"Failed to write Mode value for DDS1/2: {response}")
            
            # --- Configure DDS3 & DDS4 (Register 38) ---
            # Register 38 controls both DDS3 and DDS4.
            # - Lower 8 bits (0-7): Controls DDS3
            # - Upper 8 bits (8-15): Controls DDS4
            
            val_3 = MODE_AC if dds3_ac else MODE_DC
            val_4 = MODE_AC if dds4_ac else MODE_DC
            
            # Combine: DDS4 (upper) | DDS3 (lower)
            valeur_dds34 = val_3 | (val_4 << 8)
            
            success, response = self._communicator.send_command(f"a{self.DDS_ADDRESSES['Mode'][3]}")
            if not success:
                return OperationResult.fail(f"Failed to select Mode register for DDS3/4: {response}")
            
            success, response = self._communicator.send_command(f"d{valeur_dds34}")
            if not success:
                return OperationResult.fail(f"Failed to write Mode value for DDS3/4: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Mode"] = {
                1: "AC" if dds1_ac else "DC",
                2: "AC" if dds2_ac else "DC",
                3: "AC" if dds3_ac else "DC",
                4: "AC" if dds4_ac else "DC"
            }
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set modes failed: {str(e)}")
    
    def set_dds_gain(self, channel: int, value: int) -> OperationResult[None, str]:
        """
        COMMAND: Configure gain for a specific DDS channel.
        
        Args:
            channel: DDS channel (1-4)
            value: Gain value (0 to 16376)
            
        Returns:
            OperationResult indicating success or failure
        """
        if not (1 <= channel <= 4) or not (0 <= value <= 16376):
            return OperationResult.fail(f"Invalid parameters: channel={channel}, value={value}")
        
        try:
            addr = self.DDS_ADDRESSES["Gain"][channel]
            
            success, response = self._communicator.send_command(f"a{addr}")
            if not success:
                return OperationResult.fail(f"Failed to select Gain address: {response}")
            
            success, response = self._communicator.send_command(f"d{value}")
            if not success:
                return OperationResult.fail(f"Failed to write Gain value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Gain"][channel] = value
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set gain failed: {str(e)}")
    
    def set_dds_phase(self, channel: int, value: int) -> OperationResult[None, str]:
        """
        COMMAND: Configure phase for a specific DDS channel.
        
        Args:
            channel: DDS channel (1-4)
            value: Phase value (0 to 65535)
            
        Returns:
            OperationResult indicating success or failure
        """
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return OperationResult.fail(f"Invalid parameters: channel={channel}, value={value}")
        
        try:
            addr = self.DDS_ADDRESSES["Phase"][channel]
            success, response = self._communicator.send_command(f"a{addr}")
            print(f"[AD9106 Controller] Selected Phase address: {addr}")
            print(f"[AD9106 Controller] Sent to MCU")
            if not success:
                return OperationResult.fail(f"Failed to select Phase address: {response}")
            
            success, response = self._communicator.send_command(f"d{value}")
            print(f"[AD9106 Controller] Sent to MCU Phase value: {value}")
            if not success:
                return OperationResult.fail(f"Failed to write Phase value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Phase"][channel] = value
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set phase failed: {str(e)}")
    
    def set_dds_offset(self, channel: int, value: int) -> OperationResult[None, str]:
        """
        COMMAND: Configure offset for a specific DDS channel.
        
        Args:
            channel: DDS channel (1-4)
            value: Offset value (0 to 65535)
            
        Returns:
            OperationResult indicating success or failure
        """
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return OperationResult.fail(f"Invalid parameters: channel={channel}, value={value}")
        
        try:
            addr = self.DDS_ADDRESSES["Offset"][channel]
            
            success, response = self._communicator.send_command(f"a{addr}")
            if not success:
                return OperationResult.fail(f"Failed to select Offset address: {response}")
            
            success, response = self._communicator.send_command(f"d{value}")
            if not success:
                return OperationResult.fail(f"Failed to write Offset value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Offset"][channel] = value
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set offset failed: {str(e)}")
    
    def set_dds_const(self, channel: int, value: int) -> OperationResult[None, str]:
        """
        COMMAND: Configure DC constant for a specific DDS channel.
        
        Args:
            channel: DDS channel (1-4)
            value: DC constant value (0 to 65535)
            
        Returns:
            OperationResult indicating success or failure
        """
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return OperationResult.fail(f"Invalid parameters: channel={channel}, value={value}")
        
        try:
            addr = self.DDS_ADDRESSES["Const"][channel]
            
            success, response = self._communicator.send_command(f"a{addr}")
            if not success:
                return OperationResult.fail(f"Failed to select Const address: {response}")
            
            success, response = self._communicator.send_command(f"d{value}")
            if not success:
                return OperationResult.fail(f"Failed to write Const value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Const"][channel] = value
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set const failed: {str(e)}")
    
    def set_dds_channel_mode(self, channel: int, mode: str) -> OperationResult[None, str]:
        """
        COMMAND: Set mode (AC/DC) for a single DDS channel without affecting others.
        
        Handles shared registers (DDS1/DDS2 share register 39, DDS3/DDS4 share register 38).
        
        Args:
            channel: DDS channel (1-4)
            mode: "AC" or "DC"
            
        Returns:
            OperationResult indicating success or failure
        """
        if channel not in [1, 2, 3, 4] or mode not in ["AC", "DC"]:
            return OperationResult.fail(f"Invalid parameters: channel={channel}, mode={mode}")
        
        try:
            MODE_AC = 0x31
            MODE_DC = 0x01
            
            target_val = MODE_AC if mode == "AC" else MODE_DC
            
            # Determine partner channel (1<->2, 3<->4)
            if channel in [1, 2]:
                other_channel = 2 if channel == 1 else 1
            else:
                other_channel = 4 if channel == 3 else 3
            
            # Get current mode of the partner channel from memory state
            other_mode_str = self._memory_state["DDS"]["Mode"][other_channel]
            other_val = MODE_AC if other_mode_str == "AC" else MODE_DC
            
            # Combine values based on channel position
            # Odd channels (1, 3) are Lower Byte (no shift)
            # Even channels (2, 4) are Upper Byte (shift << 8)
            if channel % 2 != 0: # Odd channel (1 or 3) -> Lower Byte
                valeur = target_val | (other_val << 8)
            else: # Even channel (2 or 4) -> Upper Byte
                valeur = other_val | (target_val << 8)
            
            # Get address from dictionary
            addr = self.DDS_ADDRESSES['Mode'][channel]
            
            success, response = self._communicator.send_command(f"a{addr}")
            if not success:
                return OperationResult.fail(f"Failed to select Mode register: {response}")
            
            success, response = self._communicator.send_command(f"d{valeur}")
            if not success:
                return OperationResult.fail(f"Failed to write Mode value: {response}")
            
            # Update memory state
            self._memory_state["DDS"]["Mode"][channel] = mode
            
            return OperationResult.ok(None)
            
        except Exception as e:
            return OperationResult.fail(f"Set channel mode failed: {str(e)}")
    
    # ==========================================================================
    # QUERIES
    # ==========================================================================
    
    def get_memory_state(self) -> Dict:
        """
        QUERY: Get current hardware configuration state.
        
        Returns:
            Copy of memory_state dictionary
        """
        import copy
        return copy.deepcopy(self._memory_state)
    
    # ==========================================================================
    # UTILITY METHODS (Internal)
    # ==========================================================================
    
    def _freq_to_uint32(self, freq_hz: float) -> Tuple[bool, int]:
        """
        Convert frequency (Hz) to 32-bit unsigned integer for AD9106.
        
        Formula: uint32 = freq * (2^32) / 16_000_000
        
        Args:
            freq_hz: Frequency in Hz
            
        Returns:
            (success, uint32_value) or (False, error_message)
        """
        resultat = freq_hz * (2**32) / self.DDS_CLOCK_FREQ_HZ
        resultat_entier = int(round(resultat))
        
        if not (0 <= resultat_entier <= 4294967295):
            return False, f"Frequency {freq_hz} Hz results in out-of-range value {resultat_entier}"
        
        return True, resultat_entier
    
    def _uint32_to_freq(self, uint32_value: int) -> float:
        """
        Convert 32-bit unsigned integer to frequency (Hz).
        
        Formula: freq = uint32 * 16_000_000 / (2^32)
        
        Args:
            uint32_value: 32-bit unsigned integer
            
        Returns:
            Frequency in Hz
        """
        freq = uint32_value * self.DDS_CLOCK_FREQ_HZ / (2**32)
        return freq
    
    def _decomposer_uint32(self, valeur_32bits: int) -> Tuple[bool, Tuple[int, int]]:
        """
        Decompose 32-bit integer into MSB (16 bits) and LSB (16 bits).
        
        Args:
            valeur_32bits: 32-bit unsigned integer
            
        Returns:
            (success, (msb, lsb)) or (False, error_message)
        """
        if not (0 <= valeur_32bits <= 4294967295):
            return False, f"Value {valeur_32bits} out of uint32 range"
        
        partie_haute = (valeur_32bits >> 16) & 0xFFFF
        partie_basse = valeur_32bits & 0xFFFF
        
        return True, (partie_haute, partie_basse)
    
    def _update_memory_from_address(self, address: int, value: int) -> None:
        """
        Update memory_state based on register address and value.
        
        Args:
            address: Register address
            value: Register value
        """
        # Frequency (MSB and LSB)
        if address == 63:  # LSB
            self._freq_lsb = value
            if self._freq_msb is not None:
                freq_uint32 = (self._freq_msb << 16) | self._freq_lsb
                self._memory_state["DDS"]["Frequence"] = int(round(self._uint32_to_freq(freq_uint32)))
        elif address == 62:  # MSB
            self._freq_msb = value
            if self._freq_lsb is not None:
                freq_uint32 = (self._freq_msb << 16) | self._freq_lsb
                self._memory_state["DDS"]["Frequence"] = int(round(self._uint32_to_freq(freq_uint32)))
        
        # Modes
        # Modes
        elif address == 38:  # Mode DDS3+DDS4 (Mode_3_4)
            # Lower 8 bits: DDS3, Upper 8 bits: DDS4
            MODE_AC = 0x31
            mode_dds3 = "AC" if (value & 0xFF) == MODE_AC else "DC"
            mode_dds4 = "AC" if ((value >> 8) & 0xFF) == MODE_AC else "DC"
            self._memory_state["DDS"]["Mode"][3] = mode_dds3
            self._memory_state["DDS"]["Mode"][4] = mode_dds4
        elif address == 39:  # Mode DDS1+DDS2 (Mode_1_2)
            # Lower 8 bits: DDS1, Upper 8 bits: DDS2
            MODE_AC = 0x31
            mode_dds1 = "AC" if (value & 0xFF) == MODE_AC else "DC"
            mode_dds2 = "AC" if ((value >> 8) & 0xFF) == MODE_AC else "DC"
            self._memory_state["DDS"]["Mode"][1] = mode_dds1
            self._memory_state["DDS"]["Mode"][2] = mode_dds2
        
        # Offsets
        elif address == 34:  # DAC4DOF
            self._memory_state["DDS"]["Offset"][4] = value
        elif address == 35:  # DAC3DOF
            self._memory_state["DDS"]["Offset"][3] = value
        elif address == 36:  # DAC2DOF
            self._memory_state["DDS"]["Offset"][2] = value
        elif address == 37:  # DAC1DOF
            self._memory_state["DDS"]["Offset"][1] = value
        
        # Constants
        elif address == 49:  # Const_1
            self._memory_state["DDS"]["Const"][1] = value
        elif address == 48:  # Const_2
            self._memory_state["DDS"]["Const"][2] = value
        elif address == 47:  # Const_3
            self._memory_state["DDS"]["Const"][3] = value
        elif address == 46:  # Const_4
            self._memory_state["DDS"]["Const"][4] = value
        
        # Gains
        elif address == 53:  # Gain_1
            self._memory_state["DDS"]["Gain"][1] = value
        elif address == 52:  # Gain_2
            self._memory_state["DDS"]["Gain"][2] = value
        elif address == 51:  # Gain_3
            self._memory_state["DDS"]["Gain"][3] = value
        elif address == 50:  # Gain_4
            self._memory_state["DDS"]["Gain"][4] = value
        
        # Phases
        elif address == 67:  # Phase_1
            self._memory_state["DDS"]["Phase"][1] = value
        elif address == 66:  # Phase_2
            self._memory_state["DDS"]["Phase"][2] = value
        elif address == 65:  # Phase_3
            self._memory_state["DDS"]["Phase"][3] = value
        elif address == 64:  # Phase_4
            self._memory_state["DDS"]["Phase"][4] = value
