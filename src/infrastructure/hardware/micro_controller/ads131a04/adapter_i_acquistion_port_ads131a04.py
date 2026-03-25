"""
ADS131A04 Acquisition Adapter - Infrastructure Layer

Responsibility:
- Implement IAcquisitionPort interface
- Translate domain concepts (MeasurementUncertainty) into hardware configuration
- Manage ADC hardware communication
- Convert raw ADC data to domain VoltageMeasurement

Rationale:
- Separates domain logic from hardware details
- Allows domain to remain independent of specific ADC model
- Encapsulates hardware-specific calculations (gain, OSR, sampling rate)

Design:
- Hexagonal Architecture: Adapter pattern
- Translates MeasurementUncertainty → ADCHardwareConfig
- Formula: Uncertainty ≈ Vref / (2^N · Gain · √OSR) + other sources
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any, List
import math

from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
import json
import os


@dataclass
class ADCHardwareConfig:
    """
    Hardware-specific ADC configuration.
    This is infrastructure, NOT domain.
    """
    channel_gains: Dict[int, int]  # PGA gains per channel (1,2,4,8,16,32,64,128)
    oversampling_ratio: int  # OSR (averaging done by ADC hardware)
    reference_voltage: float  # Vref (V)
    sampling_rate_hz: float  # Output data rate after decimation


class ADS131A04Adapter(IAcquisitionPort):
    """
    Infrastructure adapter for ADS131A04 ADC.
    Implements IAcquisitionPort interface.
    Translates domain concepts to hardware configuration via MCU serial communication.
    """
    
    # ADS131A04 specifications
    ADC_RESOLUTION_BITS = 24
    DEFAULT_VREF = 2.5  # Volts
    AVAILABLE_GAINS = [1, 2, 4, 8, 16, 32, 64, 128]
    # OSR values from datasheet Table 30. Data Rate Settings
    AVAILABLE_OSR = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
    MAX_DATA_RATE_HZ = 128000  # Maximum output data rate
    
    def __init__(self, serial_communicator):
        """
        Args:
            serial_communicator: MCU_serial_communicator (singleton)
        """
        self._serial = serial_communicator
        self._current_config: Optional[ADCHardwareConfig] = None
    
    def load_config(self, config_dict: dict) -> None:
        """
        Load hardware configuration from a dictionary (typically parsed from JSON).
        
        Args:
            config_dict: Dictionary containing ADC configuration.
        """
        try:
            # If config is nested under 'adc', unwrap it. Otherwise use as is.
            adc_config = config_dict.get("adc", config_dict)
            
            # Parse gains
            # JSON keys are strings ("1"), convert to int
            channels = adc_config["channels"]
            channel_gains = {}
            for ch_str, ch_settings in channels.items():
                channel_gains[int(ch_str)] = ch_settings["gain"]
            
            self._current_config = ADCHardwareConfig(
                channel_gains=channel_gains,
                oversampling_ratio=adc_config["oversampling_ratio"],
                reference_voltage=adc_config["reference_voltage"],
                # Calculate sampling rate based on OSR (approximate)
                sampling_rate_hz=self.MAX_DATA_RATE_HZ / adc_config["oversampling_ratio"]
            )
            print(f"[ADS131Adapter] Configuration loaded: {self._current_config}")
            
        except KeyError as e:
            print(f"[ADS131Adapter] Failed to load config: Missing key {e}")
            raise ValueError(f"Invalid configuration format: Missing key {e}")
        except Exception as e:
            print(f"[ADS131Adapter] Failed to load config: {e}")
            raise e
    
    def acquire_sample(self) -> VoltageMeasurement:
        """
        Acquire one voltage measurement sample via MCU.
        
        The ADC has already performed hardware averaging (OSR).
        The MCU performs additional software averaging (n_avg) before returning data.
        This returns one averaged sample.
        
        Returns:
            VoltageMeasurement in domain language
            
        Raises:
            RuntimeError: If acquisition or parsing fails
        """
        from datetime import datetime
        import json
        import os
        
        # Get n_avg from MCU config (default: 1)
        n_avg = 1
        try:
            mcu_config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "mcu_last_config.json"
            )
            if os.path.exists(mcu_config_path):
                with open(mcu_config_path, 'r') as f:
                    mcu_config = json.load(f)
                    n_avg = int(mcu_config.get("n_avg", 1))
        except Exception as e:
            print(f"[ADS131Adapter] Failed to read MCU config, using default n_avg=1: {e}")
        
        # Acquire via MCU: command 'm{n_avg}' (n_avg samples averaged by MCU)
        # DEBUG: Trace acquisition start
        # print(f"[ADS131Adapter] Requesting sample 'm{n_avg}'")
        success, response = self._serial.send_command(f'm{n_avg}')
        
        if not success:
            print(f"[ADS131Adapter] Acquisition failed. Response: {response}")
            raise RuntimeError(f"Acquisition failed: {response}")

        # Parse response: tab-separated raw ADC codes (8 channels hardware, use first 6)
        try:
            raw_codes = [int(x) for x in response.split('\t') if x.strip()]
            
            if len(raw_codes) < 6:
                print(f"[ADS131Adapter] Error: Not enough channels. Got {len(raw_codes)}")
                raise ValueError(f"Expected at least 6 channels, got {len(raw_codes)}")
            # Use only first 6 channels
            raw_codes = raw_codes[:6]
        except ValueError as e:
            print(f"[ADS131Adapter] Parsing error: {e}")
            raise RuntimeError(f"Failed to parse ADC data: {e}, response: '{response}'")
        
        # Convert raw codes to voltages
        return VoltageMeasurement(
            voltage_x_in_phase=self._convert_raw_to_volts(raw_codes[0], channel=1),
            voltage_x_quadrature=self._convert_raw_to_volts(raw_codes[1], channel=2),
            voltage_y_in_phase=self._convert_raw_to_volts(raw_codes[2], channel=3),
            voltage_y_quadrature=self._convert_raw_to_volts(raw_codes[3], channel=4),
            voltage_z_in_phase=self._convert_raw_to_volts(raw_codes[4], channel=5),
            voltage_z_quadrature=self._convert_raw_to_volts(raw_codes[5], channel=6),
            timestamp=datetime.now(),
            uncertainty_estimate_volts=self._estimate_uncertainty()
        )
    
    def _convert_raw_to_volts(self, raw_code: int, channel: int) -> float:
        """
        Convert raw 24-bit signed ADC code to volts.
        
        Args:
            raw_code: Raw ADC reading (24-bit signed integer [-8388608, 8388607])
            channel: Channel number (1-6)
        
        Returns:
            Voltage in volts
            
        Raises:
            ValueError: If raw_code out of valid 24-bit range
            RuntimeError: If ADC not configured
        """
        # Validate 24-bit signed range
        if not (-8388608 <= raw_code <= 8388607):
            raise ValueError(f"Invalid 24-bit ADC code: {raw_code}")
        
        if self._current_config is None:
            raise RuntimeError("ADC not configured")
        
        gain = self._current_config.channel_gains[channel]
        vref = self._current_config.reference_voltage
        
        # ADS131A04 conversion formula (datasheet)
        # V = (raw / 2^23) * (Vref / Gain)
        # 2^23 because 24-bit signed (one bit for sign)
        voltage = (raw_code / (2**23)) * (vref / gain)
        
        return voltage
    
    def _estimate_uncertainty(self) -> float:
        """
        Estimate current measurement uncertainty based on configuration.
        
        For now, this primarily estimates quantization uncertainty.
        Could be extended to include other uncertainty sources.
        
        Returns:
            Estimated measurement uncertainty in volts (±V)
        """
        if self._current_config is None:
            return 0.0
        
        vref = self._current_config.reference_voltage
        gain = list(self._current_config.channel_gains.values())[0]  # Assume same for all
        osr = self._current_config.oversampling_ratio
        
        # Uncertainty (quantization component) = Vref / (2^N · Gain · √OSR)
        uncertainty = vref / (2**self.ADC_RESOLUTION_BITS * gain * math.sqrt(osr))
        
        return uncertainty
    
    def is_ready(self) -> bool:
        """Check if ADC is ready for acquisition."""
        return self._current_config is not None

    def is_ready(self) -> bool:
        """Check if ADC is ready for acquisition."""
        return self._current_config is not None

