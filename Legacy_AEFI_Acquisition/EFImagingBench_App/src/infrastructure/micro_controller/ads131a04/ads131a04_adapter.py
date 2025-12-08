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
from typing import Dict, Optional
import math

from ....domain.ports.i_acquisition_port import IAcquisitionPort
from ....domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from ....domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


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
    AVAILABLE_OSR = [128, 256, 512, 1024, 2048, 4096, 8192, 16384]
    MAX_DATA_RATE_HZ = 128000  # Maximum output data rate
    
    def __init__(self, serial_communicator):
        """
        Args:
            serial_communicator: MCU_serial_communicator (singleton)
        """
        self._serial = serial_communicator
        self._current_config: Optional[ADCHardwareConfig] = None
    
    def configure_for_uncertainty(self, uncertainty: MeasurementUncertainty) -> None:
        """
        Configure ADC hardware to achieve target measurement uncertainty.
        
        This is where the domain concept (uncertainty) is translated
        into hardware parameters (gain, OSR, Vref).
        
        Args:
            uncertainty: Domain concept of acceptable measurement uncertainty
        """
        # Calculate optimal hardware configuration
        hw_config = self._calculate_hardware_config_for_uncertainty(uncertainty)
        
        # Apply to hardware
        self._apply_hardware_config(hw_config)
        
        # Store current configuration
        self._current_config = hw_config
    
    def _calculate_hardware_config_for_uncertainty(
        self, 
        uncertainty: MeasurementUncertainty
    ) -> ADCHardwareConfig:
        """
        Calculate optimal ADC configuration to achieve target uncertainty.
        
        Uncertainty sources:
        - Quantization: Q_noise = Vref / (2^N · Gain · √OSR)
        - Thermal noise, calibration errors, etc. (handled by infrastructure)
        
        For now, we primarily address quantization noise.
        
        Args:
            uncertainty: Target measurement uncertainty
        
        Returns:
            Hardware configuration to achieve target uncertainty
        """
        vref = self.DEFAULT_VREF
        target_uncertainty = uncertainty.max_uncertainty_volts
        
        # Calculate required effective bits
        # ENOB = log2(Vref / uncertainty)
        required_enob = uncertainty.effective_number_of_bits(vref)
        
        # Select optimal gain
        # Start with moderate gain (8) as default
        # TODO: This should be based on expected signal amplitude
        optimal_gain = 8
        
        # Calculate required OSR
        # Uncertainty ≈ Vref / (2^N · Gain · √OSR)
        # OSR = (Vref / (uncertainty · 2^N · Gain))^2
        lsb_without_osr = vref / (2**self.ADC_RESOLUTION_BITS * optimal_gain)
        required_osr = (lsb_without_osr / target_uncertainty) ** 2
        
        # Select closest available OSR
        optimal_osr = self._select_closest_osr(required_osr)
        
        # Calculate output sampling rate
        # Data rate = Master clock / OSR
        # For simplicity, use maximum rate / OSR
        output_rate = self.MAX_DATA_RATE_HZ / optimal_osr
        
        return ADCHardwareConfig(
            channel_gains={ch: optimal_gain for ch in range(1, 7)},  # 6 channels
            oversampling_ratio=optimal_osr,
            reference_voltage=vref,
            sampling_rate_hz=output_rate
        )
    
    def _select_closest_osr(self, target_osr: float) -> int:
        """Select closest available OSR value."""
        if target_osr <= self.AVAILABLE_OSR[0]:
            return self.AVAILABLE_OSR[0]
        if target_osr >= self.AVAILABLE_OSR[-1]:
            return self.AVAILABLE_OSR[-1]
        
        # Find closest
        closest = min(self.AVAILABLE_OSR, key=lambda x: abs(x - target_osr))
        return closest
    
    def _apply_hardware_config(self, config: ADCHardwareConfig) -> None:
        """
        Apply hardware configuration to ADC via MCU serial commands.
        
        Args:
            config: Hardware configuration to apply
        """
        # TODO: Implement MCU commands for:
        # - set_iclk_divider_and_oversampling (via a14/d commands)
        # - set_reference_config (via a11/d commands)
        # - per-channel gain configuration
        
        # For now, configuration is placeholder
        # MCU firmware needs to expose these configuration commands
        pass
    
    def acquire_sample(self) -> VoltageMeasurement:
        """
        Acquire one voltage measurement sample via MCU.
        
        The ADC has already performed hardware averaging (OSR).
        This returns one averaged sample.
        
        Returns:
            VoltageMeasurement in domain language
            
        Raises:
            RuntimeError: If acquisition or parsing fails
        """
        from datetime import datetime
        
        # Acquire via MCU: command 'm1' (1 sample averaged)
        success, response = self._serial.send_command('m1')
        
        if not success:
            raise RuntimeError(f"Acquisition failed: {response}")
        
        # Parse response: tab-separated raw ADC codes (8 channels hardware, use first 6)
        try:
            raw_codes = [int(x) for x in response.split('\t') if x.strip()]
            if len(raw_codes) < 6:
                raise ValueError(f"Expected at least 6 channels, got {len(raw_codes)}")
            # Use only first 6 channels
            raw_codes = raw_codes[:6]
        except ValueError as e:
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
