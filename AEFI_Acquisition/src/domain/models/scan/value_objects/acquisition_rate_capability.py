"""
Acquisition Rate Capability - Value Object

Represents the MEASURED acquisition capability of the hardware system,
not a requested configuration.

Responsibility:
- Encapsulate measured acquisition rate with uncertainty
- Determine if capability is sufficient for FlyScan requirements
- Validate temporal stability
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AcquisitionRateCapability:
    """
    Measured acquisition rate capability of the hardware system.

    This is NOT a configuration - it's a measurement result.

    Attributes:
        measured_rate_hz: Mean acquisition rate measured from hardware (Hz)
        measured_std_dev_hz: Standard deviation of acquisition rate (Hz)
        measurement_timestamp: When this measurement was taken
        measurement_duration_s: Duration of measurement (longer = more reliable)
        sample_count: Number of samples used for measurement
        configuration_hash: Hash of hardware config when measured (for invalidation)
    """

    measured_rate_hz: float
    measured_std_dev_hz: float
    measurement_timestamp: datetime
    measurement_duration_s: float
    sample_count: int
    configuration_hash: Optional[str] = None

    def __post_init__(self):
        """Validate measurement."""
        if self.measured_rate_hz <= 0:
            raise ValueError("Measured rate must be positive")
        if self.measured_std_dev_hz < 0:
            raise ValueError("Standard deviation must be non-negative")
        if self.measurement_duration_s <= 0:
            raise ValueError("Measurement duration must be positive")
        if self.sample_count < 10:
            raise ValueError("Measurement requires at least 10 samples")

    def get_coefficient_of_variation(self) -> float:
        """
        Calculate coefficient of variation (CV = std_dev / mean).

        Lower CV = more stable rate.

        Returns:
            CV as percentage (0-100+)
        """
        return (self.measured_std_dev_hz / self.measured_rate_hz) * 100

    def is_stable_for_flyscan(self, max_cv_percent: float = 5.0) -> bool:
        """
        Determine if acquisition rate is stable enough for FlyScan.

        FlyScan requires stable timing to accurately predict positions.

        Args:
            max_cv_percent: Maximum acceptable coefficient of variation (%)

        Returns:
            True if stable enough, False otherwise
        """
        return self.get_coefficient_of_variation() <= max_cv_percent

    def get_minimum_guaranteed_rate_hz(self, confidence_sigma: float = 3.0) -> float:
        """
        Calculate minimum guaranteed rate (mean - N*sigma).

        Used for conservative FlyScan planning.

        Args:
            confidence_sigma: Number of standard deviations below mean

        Returns:
            Minimum guaranteed rate (Hz)
        """
        min_rate = self.measured_rate_hz - (confidence_sigma * self.measured_std_dev_hz)
        return max(min_rate, 0.0)  # Can't be negative

    def get_maximum_spacing_for_motion(
        self,
        motion_speed_mm_s: float,
        confidence_sigma: float = 3.0
    ) -> float:
        """
        Calculate maximum spacing between acquisition points during motion.

        Uses minimum guaranteed rate for conservative estimate.

        Args:
            motion_speed_mm_s: Motion speed (mm/s)
            confidence_sigma: Number of standard deviations for guarantee

        Returns:
            Maximum spacing between samples (mm)
        """
        min_rate = self.get_minimum_guaranteed_rate_hz(confidence_sigma)
        if min_rate <= 0:
            return float('inf')  # No guarantee possible

        return motion_speed_mm_s / min_rate

    def is_measurement_recent(self, max_age_seconds: float = 300.0) -> bool:
        """
        Check if measurement is recent enough to be trusted.

        Args:
            max_age_seconds: Maximum age before re-measurement recommended

        Returns:
            True if recent, False if stale
        """
        age = (datetime.now() - self.measurement_timestamp).total_seconds()
        return age <= max_age_seconds

    def __str__(self) -> str:
        """Human-readable representation."""
        cv = self.get_coefficient_of_variation()
        return (
            f"AcquisitionRateCapability("
            f"rate={self.measured_rate_hz:.1f}±{self.measured_std_dev_hz:.1f} Hz, "
            f"CV={cv:.2f}%, "
            f"samples={self.sample_count}, "
            f"duration={self.measurement_duration_s:.1f}s"
            f")"
        )
