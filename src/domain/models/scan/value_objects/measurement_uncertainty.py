"""
Measurement Uncertainty Value Object

Represents the domain concept of measurement uncertainty as a voltage range.
This is a business concept that abstracts away hardware details (ADC gains, OSR, etc.).

Responsibility:
- Define the acceptable uncertainty range for measurements
- Provide domain-level validation
- Express precision requirements in domain units (Volts)

Rationale:
- Physicists and researchers think in terms of "uncertainty" and "measurement range"
- Uncertainty can come from multiple sources (quantization, noise, calibration, etc.)
- Infrastructure determines how to achieve the target uncertainty
- Domain only specifies the acceptable range in Volts

Design:
- Immutable value object (frozen dataclass)
- Self-validating
- Uncertainty expressed in domain units (Volts), not hardware parameters
"""

from dataclasses import dataclass
from typing import Optional
import math

from domain.models.scan.value_objects.data_validation_result import DataValidationResult


@dataclass(frozen=True)
class MeasurementUncertainty:
    """
    Domain concept: acceptable measurement uncertainty expressed as a voltage range.
    
    The uncertainty represents the maximum acceptable deviation from the true value.
    Infrastructure determines how to achieve this (via ADC configuration, averaging, etc.).
    
    Attributes:
        max_uncertainty_volts: Maximum acceptable measurement uncertainty (±V)
            This is a ± range, e.g., 10µV means the measurement can vary by ±10µV
    
    Example:
        >>> uncertainty = MeasurementUncertainty(max_uncertainty_volts=10e-6)  # ±10 µV
        >>> # Infrastructure will configure ADC to achieve this uncertainty
    """
    
    max_uncertainty_volts: float  # Maximum acceptable uncertainty (±V)
    
    def __post_init__(self):
        """Validate at construction time"""
        result = self.validate()
        if not result.is_valid:
            raise ValueError(f"Invalid MeasurementPrecision: {', '.join(result.errors)}")
    
    def validate(self) -> DataValidationResult:
        """
        Validate measurement uncertainty constraints.
        
        Returns:
            DataValidationResult with validation status and error messages
        """
        errors = []
        warnings = []
        
        # Uncertainty must be positive
        if self.max_uncertainty_volts <= 0:
            errors.append("Measurement uncertainty must be positive")
        
        # Typical range checks (warnings only)
        if self.max_uncertainty_volts < 1e-9:  # < 1 nV
            warnings.append("Uncertainty < 1nV may be unrealistic with current hardware")
        
        if self.max_uncertainty_volts > 1e-3:  # > 1 mV
            warnings.append("Uncertainty > 1mV may be too coarse for precise measurements")
        
        return DataValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def effective_number_of_bits(self, signal_range_volts: float) -> float:
        """
        Calculate Effective Number Of Bits (ENOB) for given signal range.
        
        This is a utility calculation that can help infrastructure determine
        the required ADC configuration.
        
        ENOB = log2(signal_range / uncertainty)
        
        Args:
            signal_range_volts: Full-scale signal range (V)
        
        Returns:
            Effective number of bits required
        
        Example:
            >>> uncertainty = MeasurementUncertainty(max_uncertainty_volts=10e-6)
            >>> uncertainty.effective_number_of_bits(2.5)
            17.93  # bits
        """
        if signal_range_volts <= 0:
            raise ValueError("Signal range must be positive")
        
        return math.log2(signal_range_volts / self.max_uncertainty_volts)
    
    def required_samples_for_snr(self, target_snr_db: float, base_snr_db: float) -> int:
        """
        Calculate number of samples to average to achieve target SNR.
        
        SNR improvement with averaging: SNR_avg = SNR_base + 10*log10(N)
        
        Args:
            target_snr_db: Target SNR in dB
            base_snr_db: Base SNR of single sample in dB
        
        Returns:
            Number of samples to average
        """
        snr_improvement_db = target_snr_db - base_snr_db
        if snr_improvement_db <= 0:
            return 1
        
        n_samples = 10 ** (snr_improvement_db / 10)
        return max(1, int(math.ceil(n_samples)))
