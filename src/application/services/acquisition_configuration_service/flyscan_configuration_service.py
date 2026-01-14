"""
FlyScan Configuration Service - Application Layer

Responsibility:
- Validate FlyScan configurations against hardware capabilities
- Suggest compatible motion profiles
"""

from typing import Tuple
from dataclasses import replace

from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
from domain.models.scan.value_objects.data_validation_result import DataValidationResult
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class FlyScanConfigurationService:
    """Application service for FlyScan configuration validation."""

    def validate_flyscan_config(
        self,
        config: FlyScanConfig,
        capability: AcquisitionRateCapability
    ) -> DataValidationResult:
        """Validate FlyScan configuration against measured capability."""
        result = config.validate_with_capability(capability)

        if result.is_valid:
            print(f"[FlyScanConfiguration] Configuration VALID")
            for warning in result.warnings:
                print(f"  WARNING: {warning}")
        else:
            print(f"[FlyScanConfiguration] Configuration INVALID")
            for error in result.errors:
                print(f"  ERROR: {error}")

        return result

    def suggest_compatible_motion_profile(
        self,
        config: FlyScanConfig,
        capability: AcquisitionRateCapability
    ) -> MotionProfile:
        """Suggest motion profile compatible with hardware capability."""
        original_profile = config.motion_profile

        # Calculate max safe speed
        guaranteed_rate = capability.get_minimum_guaranteed_rate_hz(confidence_sigma=3.0)
        max_safe_speed = config.max_spatial_gap_mm * guaranteed_rate

        if original_profile.target_speed <= max_safe_speed:
            return original_profile

        # Scale down
        speed_ratio = max_safe_speed / original_profile.target_speed

        suggested_profile = MotionProfile(
            min_speed=original_profile.min_speed * speed_ratio,
            target_speed=max_safe_speed,
            acceleration=original_profile.acceleration * speed_ratio,
            deceleration=original_profile.deceleration * speed_ratio
        )

        print(f"[FlyScanConfiguration] Suggested slower profile: "
              f"{original_profile.target_speed}mm/s → {max_safe_speed:.1f}mm/s")

        return suggested_profile

    def estimate_flyscan_duration(
        self,
        config: FlyScanConfig,
        capability: AcquisitionRateCapability
    ) -> Tuple[float, int]:
        """
        Estimate FlyScan duration and point count.

        Returns:
            (estimated_duration_seconds, estimated_point_count)
        """
        x_dist = config.scan_zone.x_max - config.scan_zone.x_min
        y_dist = config.scan_zone.y_max - config.scan_zone.y_min

        total_distance = (x_dist * config.y_nb_points) + (y_dist * (config.y_nb_points - 1))

        avg_speed = (config.motion_profile.min_speed + config.motion_profile.target_speed) / 2
        estimated_duration = total_distance / avg_speed if avg_speed > 0 else 0

        estimated_points = int(estimated_duration * capability.measured_rate_hz)

        return (estimated_duration, estimated_points)
