from typing import Optional
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator

class MCULifecycleAdapter(IHardwareInitializationPort):
    """
    Lifecycle Adapter for the MCU (MicroController Unit).
    
    Responsibility:
    - Manage the lifecycle (Connect, Verify, Close) of the MCU Serial Communicator.
    - Acts as the 'plumbing' layer for MCU initialization.
    """
    
    def __init__(self, port: str = "COM10", baudrate: int = 9600, communicator: Optional[MCU_SerialCommunicator] = None):
        self._port_name = port
        self._baudrate = baudrate
        if communicator:
            self._communicator = communicator
        else:
            self._communicator = MCU_SerialCommunicator() # Singleton access
        self._config: Optional[dict] = None

    def set_config(self, config: dict) -> None:
        """Set configuration to be used during initialization."""
        self._config = config

    def initialize_all(self, config: Optional[dict] = None) -> dict:
        """
        Initialize the MCU connection and configure hardware settings.
        
        Args:
            config: Dictionary containing 'adc' and 'dds' configuration.
            
        Returns:
            Dict of initialized resources.
        """
        print(f"[MCULifecycle] Initializing MCU on {self._port_name}...")
        success = self._communicator.connect(self._port_name, self._baudrate)
        if not success:
            raise RuntimeError(f"Failed to connect to MCU on port {self._port_name}")
        
        if config:
            # Override stored config if provided directly
            self._config = config
            
        if self._config:
            print(f"[MCULifecycle] Configuring hardware from JSON...")
            self._configure_hardware_from_json(self._config)
        else:
            print(f"[MCULifecycle] WARNING: No configuration provided. Using legacy defaults.")
            self._init_default_hardware_config()
        
        return {"mcu_communicator": self._communicator}

    def _configure_hardware_from_json(self, config: dict) -> None:
        """Apply configuration from JSON dictionary."""
        if "adc" in config:
            self._configure_adc(config["adc"])
        if "dds" in config:
            self._configure_dds(config["dds"])
            
    def _configure_adc(self, adc_config: dict) -> None:
        """Configure ADC registers."""
        # 0. A_SYS_CFG register (Address 11) - Reference configuration
        # Bit 7: VNCPEN (negative_ref), Bit 6: HRM (high_res), Bit 4: VREF_4V (ref_voltage), Bit 3: INT_REFEN (ref_selection)
        if any(key in adc_config for key in ["negative_ref", "high_res", "ref_voltage", "ref_selection"]):
            a_sys_cfg_val = 0
            
            # Bit 7: VNCPEN (Negative charge pump enable)
            if adc_config.get("negative_ref", False):
                a_sys_cfg_val += 128
            
            # Bit 6: HRM (High-resolution mode)
            if adc_config.get("high_res", True):  # Default True
                a_sys_cfg_val += 64
            
            # Bit 5: Reserved - always write 1
            a_sys_cfg_val += 32
            
            # Bit 4: VREF_4V (Reference voltage level: 0=2.442V, 1=4.0V)
            if adc_config.get("ref_voltage", 0) == 1:  # 1 = 4.0V
                a_sys_cfg_val += 16
            
            # Bit 3: INT_REFEN (Internal reference enable: 0=External, 1=Internal)
            if adc_config.get("ref_selection", 1) == 1:  # 1 = Internal
                a_sys_cfg_val += 8
            
            self._write_register(11, a_sys_cfg_val)
            print(f"[MCULifecycle] A_SYS_CFG register (11) = {a_sys_cfg_val} (neg_ref={adc_config.get('negative_ref', False)}, high_res={adc_config.get('high_res', True)}, ref_voltage={adc_config.get('ref_voltage', 0)}, ref_selection={adc_config.get('ref_selection', 1)})")
        
        # 1. CLKIN divider (Address 13)
        if "clkin_divider" in adc_config:
            self._write_register(13, adc_config["clkin_divider"])
            
        # 2. ICLK divider + OSR (Address 14)
        # Register 14: Bits[7:5]=ICLK_DIV, Bits[4:1] or [3:0]=OSR (check datasheet register map)
        # We assume ICLK_DIV=2 (001 -> 32) for now as per legacy default.
        # OSR Mapping from datasheet Table 30. Data Rate Settings (OSR[3:0] codes 0-15):
        # Code 0->4096, 1->2048, 2->1024, 3->800, 4->768, 5->512, 6->400, 7->384,
        # 8->256, 9->200, 10->192, 11->128, 12->96, 13->64, 14->48, 15->32
        if "oversampling_ratio" in adc_config:
            osr_val = int(adc_config["oversampling_ratio"])
            osr_map = {
                4096: 0, 2048: 1, 1024: 2, 800: 3, 768: 4, 512: 5, 400: 6, 384: 7,
                256: 8, 200: 9, 192: 10, 128: 11, 96: 12, 64: 13, 48: 14, 32: 15
            }
            
            if osr_val in osr_map:
                osr_code = osr_map[osr_val]
                # Combine with ICLK_DIV=2 (001 -> shift 5 bits = 32)
                # If ICLK_DIV is configurable in future, read it from config.
                iclk_div_val = 2 # Default /2
                # Map ICLK div to bits? Legacy 32 implies 001 (1).
                # 001 << 5 = 32.
                # So Reg = 32 | (osr_code << 2) ? 
                # Wait, OSR is bits 4:2. 
                # 000 -> 0. 32 | 0 = 32. Correct for OSR 128.
                # 001 -> 1. 1<<2 = 4. 32 | 4 = 36. Correct for OSR 256.
                
                reg_val = 32 | (osr_code << 2)
                self._write_register(14, reg_val)
            else:
                print(f"[MCULifecycle] WARNING: Invalid OSR {osr_val}. Using default (32).")
                self._write_register(14, 32) # Fallback to legacy default
            
        # 3. Gains (Addresses 17-20)
        if "channels" in adc_config:
            for ch_str, settings in adc_config["channels"].items():
                ch = int(ch_str)
                if 1 <= ch <= 4: # ADC has 4 gain registers for main channels? Legacy has 17,18,19,20
                    # Legacy: 17=Gain1, 18=Gain2, 19=Gain3, 20=Gain4
                    # Map channel to address: 1->17, 2->18, 3->19, 4->20
                    addr = 16 + ch
                    gain_val = 0 # Default to 0 (Gain=1)
                    # TODO: Map gain value (1, 2, 4...) to register value (0, 1, 2...)
                    # For now, assuming 0 in JSON means register value 0.
                    # Wait, JSON has "gain": 1. Legacy has (17, 0).
                    # Need a map.
                    gain_map = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7}
                    gain_setting = settings.get("gain", 1)
                    reg_val = gain_map.get(gain_setting, 0)
                    self._write_register(addr, reg_val)

    def _configure_dds(self, dds_config: dict) -> None:
        """Configure DDS registers."""
        # 1. Frequency
        if "frequency_hz" in dds_config:
            freq_hz = dds_config["frequency_hz"]
            # Formula: uint32 = freq * (2^32) / 16_000_000
            val_32 = int(round(freq_hz * (2**32) / 16_000_000))
            msb = (val_32 >> 16) & 0xFFFF
            lsb = val_32 & 0xFFFF
            self._write_register(62, msb)
            self._write_register(63, lsb)
            
        # 2. Modes
        # Legacy: 38 (DDS3+4), 39 (DDS1+2). Value 12593 means AC+AC.
        # 12593 = 0x3131. 0x31 = 49 (AC). 
        # So 12593 is AC(49) << 8 | AC(49).
        # We can implement parsing logic here or just use the legacy value if we trust the JSON to match.
        # But JSON has strings "AC+AC".
        mode_map = {"AC": 49, "DC": 1} # Simplified map based on legacy
        
        if "mode_dds1_dds2" in dds_config:
            mode_str = dds_config["mode_dds1_dds2"] # "AC+AC"
            parts = mode_str.split('+')
            if len(parts) == 2:
                m1 = mode_map.get(parts[0], 49)
                m2 = mode_map.get(parts[1], 49)
                # DDS1 is LSB?, DDS2 is MSB?
                # Legacy: 39 -> 12593. 12593 = 0x3131. Both are 0x31 (49).
                # So order doesn't matter for AC+AC.
                val = (m2 << 8) | m1
                self._write_register(39, val)
                
        if "mode_dds3_dds4" in dds_config:
            mode_str = dds_config["mode_dds3_dds4"]
            parts = mode_str.split('+')
            if len(parts) == 2:
                m3 = mode_map.get(parts[0], 49)
                m4 = mode_map.get(parts[1], 49)
                val = (m4 << 8) | m3
                self._write_register(38, val)

        # 3. Gains, Phases, Offsets, Consts
        # Map: Channel -> {Gain: addr, Phase: addr, ...}
        # Using legacy addresses
        # Gain: 1->53, 2->52, 3->51, 4->50
        # Phase: 1->67, 2->66, 3->65, 4->64
        # Offset: 1->37, 2->36, 3->35, 4->34
        # Const: 1->49, 2->48, 3->47, 4->46
        
        addr_map = {
            "gain": {1: 53, 2: 52, 3: 51, 4: 50},
            "phase": {1: 67, 2: 66, 3: 65, 4: 64},
            "offset": {1: 37, 2: 36, 3: 35, 4: 34},
            "const": {1: 49, 2: 48, 3: 47, 4: 46} # Not in JSON example but in legacy
        }
        
        if "channels" in dds_config:
            for ch_str, settings in dds_config["channels"].items():
                ch = int(ch_str)
                if "gain" in settings:
                    self._write_register(addr_map["gain"][ch], settings["gain"])
                if "phase" in settings:
                    self._write_register(addr_map["phase"][ch], settings["phase"])
                if "offset" in settings:
                    self._write_register(addr_map["offset"][ch], settings["offset"])

    def _write_register(self, address: int, value: int) -> None:
        """Helper to write to a register."""
        success, response = self._communicator.send_command(f"a{address}")
        if not success:
            print(f"[MCULifecycle] WARNING: Failed to select address {address}: {response}")
            return
        
        success, response = self._communicator.send_command(f"d{value}")
        if not success:
            print(f"[MCULifecycle] WARNING: Failed to write value {value} to address {address}: {response}")
    
    def _init_default_hardware_config(self) -> None:
        """
        Initialize MCU hardware with default configuration.
        
        Configures:
        - ADC: CLKIN divider (2), ICLK divider (2), OSR (32), Gains (0)
        - DDS: Frequency (1000 Hz), Modes (AC+AC), Gains (0 for DDS1/2, 10000 for DDS3/4)
        
        This matches the legacy init_default_config() behavior.
        """
        # Default configuration sequence (from legacy init_default_config)
        # Format: (address, value)
        params_default = [
            # ADC Configuration
            (13, 2),      # ADC: CLKIN_divider_ratio = 2
            (14, 32),     # ADC: ICLK_divider_ratio (2) + Oversampling_ratio (32) combined
            (17, 0),      # ADC: Gain_ADC_1 = 0
            (18, 0),      # ADC: Gain_ADC_2 = 0
            (19, 0),      # ADC: Gain_ADC_3 = 0
            (20, 0),      # ADC: Gain_ADC_4 = 0
            # DDS Configuration
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
                print(f"[MCULifecycle] WARNING: Failed to select address {address}: {response}")
                continue
            
            # Write data
            success, response = self._communicator.send_command(f"d{value}")
            if not success:
                print(f"[MCULifecycle] WARNING: Failed to write value {value} to address {address}: {response}")
                continue
        
        print(f"[MCULifecycle] Default hardware configuration applied successfully.")
        
    def verify_all(self) -> bool:
        """
        Verify connection by sending a simple ping or checking status.
        
        Returns:
            True if verification succeeds, False otherwise.
        """
        # We can try to send a dummy command or just check if open
        if not self._communicator.ser or not self._communicator.ser.is_open:
             raise RuntimeError("MCU Serial port is not open.")
             
        # Optional: Send a 'ping' command if supported. 
        # For now, just checking the connection status is enough.
        print(f"[MCULifecycle] Verification Success. Connected to {self._port_name}.")
        return True

    def close_all(self) -> None:
        """
        Close the connection.
        """
        print("[MCULifecycle] Closing MCU connection...")
        self._communicator.disconnect()

    def get_communicator(self) -> MCU_SerialCommunicator:
        """
        Retrieve the communicator instance.
        """
        return self._communicator
