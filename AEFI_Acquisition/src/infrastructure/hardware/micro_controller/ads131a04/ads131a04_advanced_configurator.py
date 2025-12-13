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
    
    # ADS131A04 specifications (from datasheet)
    # PGA Gain values: Register CHx_CFG bits [2:0] map to gains 1, 2, 4, 8, 16, 32, 64, 128
    # See datasheet section 9.6 Register Maps, CHx_CFG register
    AVAILABLE_GAINS = [1, 2, 4, 8, 16, 32, 64, 128]
    
    # OSR (Oversampling Ratio) values: Register MODE bits OSR[3:0] map to OSR values
    # See datasheet Table 30. Data Rate Settings (section 9.4 Device Functional Modes)
    # OSR determines data rate: Data Rate = fMOD / OSR
    # Values from datasheet Table 30 (ordered by OSR code 0000 to 1111):
    AVAILABLE_OSR = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
    
    # CLK_DIV and ICLK_DIV divider ratios (from datasheet register maps)
    # CLK_DIV[2:0] (bits 3:1 of CLKIN register): 2, 4, 6, 8, 10, 12, 14
    # ICLK_DIV[2:0] (bits 7:5 of MODE register): 2, 4, 6, 8, 10, 12, 14
    AVAILABLE_CLK_DIV = [2, 4, 6, 8, 10, 12, 14]
    AVAILABLE_ICLK_DIV = [2, 4, 6, 8, 10, 12, 14]
    
    # fMOD values from datasheet table based on resolution mode and VNCPEN bit
    # Format: (resolution_mode, vncpen): [fMOD values in Hz]
    FMOD_VALUES = {
        ("high_resolution", False): [0.1e6, 4.096e6, 4.25e6],  # VNCPEN=0
        ("high_resolution", True): [0.512e6, 4.096e6, 4.25e6],  # VNCPEN=1
        ("low_power", False): [0.1e6, 1.024e6, 1.05e6],  # VNCPEN=0
        ("low_power", True): [0.512e6, 1.024e6, 1.05e6],  # VNCPEN=1
    }

    @staticmethod
    def calculate_adc_output_data_frequency(
        fclkin_hz: float,
        clk_div: int,
        iclk_div: int,
        osr: int
    ) -> float:
        """
        Calculate ADC output data frequency (fDATA) from clock configuration.
        
        Formula from datasheet:
        - fICLK = fCLKIN / CLK_DIV
        - fMOD = fICLK / ICLK_DIV
        - fDATA = fMOD / OSR
        
        Therefore: fDATA = fCLKIN / (CLK_DIV × ICLK_DIV × OSR)
        
        Args:
            fclkin_hz: Input clock frequency (fCLKIN) in Hz
            clk_div: CLK_DIV divider ratio (2, 4, 6, 8, 10, 12, or 14)
            iclk_div: ICLK_DIV divider ratio (2, 4, 6, 8, 10, 12, or 14)
            osr: Oversampling ratio (one of AVAILABLE_OSR values)
        
        Returns:
            ADC output data frequency (fDATA) in Hz
        
        Raises:
            ValueError: If invalid divider or OSR values are provided
        """
        if clk_div not in ADS131A04AdvancedConfigurator.AVAILABLE_CLK_DIV:
            raise ValueError(f"Invalid CLK_DIV: {clk_div}. Must be one of {ADS131A04AdvancedConfigurator.AVAILABLE_CLK_DIV}")
        
        if iclk_div not in ADS131A04AdvancedConfigurator.AVAILABLE_ICLK_DIV:
            raise ValueError(f"Invalid ICLK_DIV: {iclk_div}. Must be one of {ADS131A04AdvancedConfigurator.AVAILABLE_ICLK_DIV}")
        
        if osr not in ADS131A04AdvancedConfigurator.AVAILABLE_OSR:
            raise ValueError(f"Invalid OSR: {osr}. Must be one of {ADS131A04AdvancedConfigurator.AVAILABLE_OSR}")
        
        if fclkin_hz <= 0:
            raise ValueError(f"Invalid fCLKIN: {fclkin_hz} Hz. Must be positive")
        
        # fDATA = fCLKIN / (CLK_DIV × ICLK_DIV × OSR)
        fdata_hz = fclkin_hz / (clk_div * iclk_div * osr)
        
        return fdata_hz

    @staticmethod
    def calculate_adc_output_data_frequency_from_resolution_mode(
        resolution_mode: str,  # "high_resolution" or "low_power"
        osr: int,
        vncpen: bool = False,  # VNCPEN bit state (default False)
        fmod_index: int = 1  # Which fMOD value to use (0, 1, or 2) - default 1 (middle value)
    ) -> float:
        """
        Calculate ADC output data frequency based on resolution mode.
        
        Uses fMOD values from datasheet table based on:
        - Resolution mode (High-resolution or Low-power)
        - VNCPEN bit state
        
        Args:
            resolution_mode: "high_resolution" or "low_power"
            osr: Oversampling ratio (one of AVAILABLE_OSR values)
            vncpen: VNCPEN bit state (default False)
            fmod_index: Index of fMOD value to use (0, 1, or 2). Default 1 (middle value)
                       0 = lowest fMOD, 1 = middle fMOD, 2 = highest fMOD
        
        Returns:
            ADC output data frequency (fDATA) in Hz
        
        Raises:
            ValueError: If invalid parameters
        """
        if resolution_mode not in ["high_resolution", "low_power"]:
            raise ValueError(f"Invalid resolution_mode: {resolution_mode}. Must be 'high_resolution' or 'low_power'")
        
        if osr not in ADS131A04AdvancedConfigurator.AVAILABLE_OSR:
            raise ValueError(f"Invalid OSR: {osr}. Must be one of {ADS131A04AdvancedConfigurator.AVAILABLE_OSR}")
        
        if fmod_index not in [0, 1, 2]:
            raise ValueError(f"Invalid fmod_index: {fmod_index}. Must be 0, 1, or 2")
        
        # Get fMOD values for this configuration
        fmod_values = ADS131A04AdvancedConfigurator.FMOD_VALUES.get((resolution_mode, vncpen))
        if fmod_values is None:
            raise ValueError(f"Invalid configuration: resolution_mode={resolution_mode}, vncpen={vncpen}")
        
        # Use the selected fMOD value
        fmod_hz = fmod_values[fmod_index]
        
        # fDATA = fMOD / OSR
        fdata_hz = fmod_hz / osr
        
        return fdata_hz

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
        
        # Global Settings - A_SYS_CFG Register (Address 11)
        # Reference Configuration (from datasheet Table 25. A_SYS_CFG Register)
        
        specs.append(BooleanParameterSchema(
            key="negative_ref",
            display_name="Negative Reference (VNCPEN)",
            description="Enable negative charge pump for 3.0-V to 3.45-V unipolar power supply. Bit 7 of A_SYS_CFG register.",
            default_value=False,
            group="Reference Configuration"
        ))
        
        specs.append(BooleanParameterSchema(
            key="high_res",
            display_name="High Resolution Mode (HRM)",
            description="High-resolution mode (better accuracy) or Low-power mode (lower power consumption). Bit 6 of A_SYS_CFG register. Affects available fMOD values.",
            default_value=True,
            group="Reference Configuration"
        ))
        
        specs.append(EnumParameterSchema(
            key="ref_voltage",
            display_name="Reference Voltage Level (VREF_4V)",
            description="REFP reference voltage level when using internal reference. Bit 4 of A_SYS_CFG register.",
            default_value="2.442V",
            choices=("2.442V", "4.0V"),
            group="Reference Configuration"
        ))
        
        specs.append(EnumParameterSchema(
            key="ref_selection",
            display_name="Reference Selection (INT_REFEN)",
            description="Internal or external reference voltage. Bit 3 of A_SYS_CFG register.",
            default_value="Internal",
            choices=("External", "Internal"),
            group="Reference Configuration"
        ))
        
        specs.append(EnumParameterSchema(
            key="oversampling_ratio",
            display_name="Oversampling Ratio (OSR)",
            description="Determines data rate and noise performance",
            default_value="4096",  # Valid OSR value (was "32" which is invalid)
            choices=tuple(str(x) for x in ADS131A04AdvancedConfigurator.AVAILABLE_OSR),
            group="Global"
        ))
        
        # Channel Settings
        # System has 2 ADS131A04 ADCs (4 channels each = 8 total), but we use 6 channels
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
        # A_SYS_CFG register parameters (legacy compatibility)
        negative_ref = bool(config.get("negative_ref", False))
        high_res = bool(config.get("high_res", True))
        ref_voltage_str = config.get("ref_voltage", "2.442V")
        ref_voltage = 1 if ref_voltage_str == "4.0V" else 0  # 0=2.442V, 1=4.0V
        ref_selection_str = config.get("ref_selection", "Internal")
        ref_selection = 1 if ref_selection_str == "Internal" else 0  # 0=External, 1=Internal
        
        # Convert high_res boolean to resolution_mode string for fMOD calculation
        resolution_mode = "high_resolution" if high_res else "low_power"
        
        json_config = {
            "clkin_divider": 2, # Fixed for now
            "iclk_divider": 2,  # Fixed for now
            "oversampling_ratio": int(config.get("oversampling_ratio", 4096)),  # Default to valid OSR value
            "resolution_mode": resolution_mode,
            "vncpen": negative_ref,  # VNCPEN = negative_ref
            # A_SYS_CFG register parameters (for hardware configuration)
            "negative_ref": negative_ref,
            "high_res": high_res,
            "ref_voltage": ref_voltage,  # 0=2.442V, 1=4.0V
            "ref_selection": ref_selection,  # 0=External, 1=Internal
            "channels": {}
        }
        
        # System has 2 ADS131A04 ADCs (4 channels each = 8 total), but we use 6 channels
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
    
    def get_adc_output_data_frequency(self) -> float:
        """
        Calculate ADC output data frequency from current configuration.
        Uses resolution mode to determine fMOD values.
        
        Returns:
            ADC output data frequency (fDATA) in Hz
        
        Raises:
            RuntimeError: If configuration has not been applied yet
        """
        # Try to get current config from adapter or last saved config
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ads131a04_last_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    # Support both old format (resolution_mode) and new format (high_res)
                    if "resolution_mode" in saved_config:
                        resolution_mode = saved_config.get("resolution_mode", "high_resolution")
                    else:
                        high_res = saved_config.get("high_res", True)
                        resolution_mode = "high_resolution" if high_res else "low_power"
                    
                    osr = saved_config.get("oversampling_ratio", 4096)
                    # Support both old format (vncpen) and new format (negative_ref)
                    vncpen = saved_config.get("vncpen", saved_config.get("negative_ref", False))
                    # Use middle fMOD value (index 1) by default
                    return self.calculate_adc_output_data_frequency_from_resolution_mode(
                        resolution_mode, osr, vncpen, fmod_index=1
                    )
        except Exception as e:
            print(f"[ADS131Configurator] Failed to read saved config: {e}")
        
        # Fallback to defaults if config not available
        return self.calculate_adc_output_data_frequency_from_resolution_mode(
            "high_resolution", 4096, False, fmod_index=1
        )
