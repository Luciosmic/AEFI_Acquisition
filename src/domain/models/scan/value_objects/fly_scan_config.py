"""
FlyScan Configuration - Value Object

Responsibility:
- Define FlyScan execution parameters
- Validate configuration against hardware capabilities
- Calculate required acquisition rate from motion parameters
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.models.scan.value_objects.data_validation_result import DataValidationResult


@dataclass(frozen=True)
class FlyScanConfig:
    """
    Configuration for fly scan execution.

    Key insight: desired_acquisition_rate_hz is a WISH, not a guarantee.
    Must be validated against measured AcquisitionRateCapability.
    """

    scan_zone: ScanZone
    x_nb_points: int
    y_nb_points: int
    scan_pattern: ScanPattern

    # Motion parameters
    motion_profile: MotionProfile  # Defines speed/acceleration

    # Acquisition parameters (DESIRED, not guaranteed)
    desired_acquisition_rate_hz: float
    max_spatial_gap_mm: float = 0.5  # Maximum acceptable gap between samples

    def __post_init__(self):
        """Validate basic configuration."""
        if self.x_nb_points < 2:
            raise ValueError("x_nb_points must be at least 2")
        if self.y_nb_points < 2:
            raise ValueError("y_nb_points must be at least 2")
        if self.desired_acquisition_rate_hz <= 0:
            raise ValueError("Desired acquisition rate must be positive")
        if self.max_spatial_gap_mm <= 0:
            raise ValueError("Max spatial gap must be positive")

    def calculate_required_minimum_rate_hz(self) -> float:
        """
        Calculate MINIMUM required acquisition rate based on motion speed
        and maximum acceptable spatial gap.

        This is a HARD CONSTRAINT - if hardware can't achieve this,
        FlyScan cannot proceed.

        Returns:
            Minimum acquisition rate (Hz) required
        """
        # Worst case: motion at maximum target speed
        max_speed = self.motion_profile.target_speed

        # To maintain max_spatial_gap_mm at max_speed:
        # gap = speed / rate
        # rate = speed / gap
        required_rate = max_speed / self.max_spatial_gap_mm

        return required_rate

    def validate_with_capability(
        self,
        capability: AcquisitionRateCapability
    ) -> DataValidationResult:
        """
        Validate this configuration against measured hardware capability.

        This is THE KEY METHOD for modeling hardware constraints.

        Args:
            capability: Measured acquisition rate capability

        Returns:
            ValidationResult indicating if configuration is feasible
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check 1: Is capability measurement recent?
        if not capability.is_measurement_recent(max_age_seconds=300):
            age_s = (datetime.now() - capability.measurement_timestamp).total_seconds()
            warnings.append(
                f"Capability measurement is stale "
                f"(age: {age_s:.0f}s). "
                f"Consider re-measuring."
            )

        # Check 2: Is acquisition rate stable enough?
        if not capability.is_stable_for_flyscan(max_cv_percent=5.0):
            cv = capability.get_coefficient_of_variation()
            warnings.append(
                f"Acquisition rate is unstable (CV={cv:.2f}%). "
                f"FlyScan position accuracy may be degraded."
            )

        # Check 3: Can hardware achieve minimum required rate?
        required_min_rate = self.calculate_required_minimum_rate_hz()
        guaranteed_rate = capability.get_minimum_guaranteed_rate_hz(confidence_sigma=3.0)

        if guaranteed_rate < required_min_rate:
            errors.append(
                f"Hardware cannot achieve required acquisition rate. "
                f"Required: {required_min_rate:.1f} Hz (for max_gap={self.max_spatial_gap_mm}mm "
                f"at speed={self.motion_profile.target_speed}mm/s). "
                f"Guaranteed: {guaranteed_rate:.1f} Hz "
                f"(measured={capability.measured_rate_hz:.1f}±{capability.measured_std_dev_hz:.1f} Hz). "
                f"Reduce motion speed or increase max_spatial_gap_mm."
            )

        # Check 4: Is desired rate achievable?
        if self.desired_acquisition_rate_hz > capability.measured_rate_hz:
            errors.append(
                f"Desired acquisition rate ({self.desired_acquisition_rate_hz:.1f} Hz) "
                f"exceeds measured capability ({capability.measured_rate_hz:.1f} Hz). "
                f"Reduce desired_acquisition_rate_hz."
            )

        # Check 5: Spatial resolution warning
        actual_spacing = capability.get_maximum_spacing_for_motion(
            self.motion_profile.target_speed,
            confidence_sigma=3.0
        )
        if actual_spacing > self.max_spatial_gap_mm:
            warnings.append(
                f"Actual spatial gap ({actual_spacing:.3f}mm) may exceed "
                f"max_spatial_gap_mm ({self.max_spatial_gap_mm}mm) "
                f"during motion at {self.motion_profile.target_speed}mm/s. "
                f"Consider slowing motion or accepting coarser resolution."
            )

        return DataValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def estimate_total_points(self, capability: AcquisitionRateCapability) -> int:
        """
        Estimate total number of acquisition points during FlyScan.

        Uses measured capability, not desired rate.

        Args:
            capability: Measured acquisition rate capability

        Returns:
            Estimated total points (may be >> x_nb_points * y_nb_points)
        """
        # Calculate total motion distance
        # (Simplified - actual depends on pattern)
        x_dist = self.scan_zone.x_max - self.scan_zone.x_min
        y_dist = self.scan_zone.y_max - self.scan_zone.y_min

        # Serpentine: x_dist * y_nb_points + y_dist * (y_nb_points-1)
        # Approximate total distance
        total_distance = (x_dist * self.y_nb_points) + (y_dist * (self.y_nb_points - 1))

        # Estimate duration
        avg_speed = (self.motion_profile.min_speed + self.motion_profile.target_speed) / 2
        estimated_duration = total_distance / avg_speed if avg_speed > 0 else 0

        # Estimate points
        estimated_points = int(estimated_duration * capability.measured_rate_hz)

        return estimated_points

    def total_grid_points(self) -> int:
        """
        Calculate total grid points (discrete positions).

        Returns:
            Total number of grid points
        """
        return self.x_nb_points * self.y_nb_points
