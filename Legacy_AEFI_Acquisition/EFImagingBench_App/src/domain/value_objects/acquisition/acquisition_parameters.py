"""
Domain: Acquisition Parameters

Responsibility:
    Configuration parameters for the ADC acquisition hardware.

Rationale:
    Encapsulates device-level configuration (averaging, gains, sampling rate).
    Immutable value object ensuring valid configuration.

Design:
    - Frozen dataclass (immutable)
    - Validation in __post_init__
    - TODO: Replace adc_gains with voltage_range (ubiquitous language)
    - TODO: Validate sampling_rate against available rates from hardware
"""
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class AcquisitionParameters:
    """ADC acquisition configuration parameters.
    
    Device-level configuration for the analog-to-digital converter.
    """
    
    # Averaging at device level (hardware/firmware)
    averaging_adc: int
    
    # Gain settings per ADC channel
    adc_gains: Dict[int, int]  # {channel_id: gain_value}
    
    # Sampling rate
    sampling_rate: float  # Hz
    
    def __post_init__(self):
        """Validate parameters."""
        if self.averaging_adc < 1:
            raise ValueError(f"averaging_adc must be >= 1, got {self.averaging_adc}")
        
        if self.sampling_rate <= 0:
            raise ValueError(f"sampling_rate must be > 0, got {self.sampling_rate}")
        
        # Validate gains dict
        if not self.adc_gains:
            raise ValueError("adc_gains cannot be empty")
        
        for ch, gain in self.adc_gains.items():
            if not isinstance(ch, int) or ch < 1:
                raise ValueError(f"Invalid channel ID: {ch}")
            if not isinstance(gain, int) or gain < 0:
                raise ValueError(f"Invalid gain for channel {ch}: {gain}")

