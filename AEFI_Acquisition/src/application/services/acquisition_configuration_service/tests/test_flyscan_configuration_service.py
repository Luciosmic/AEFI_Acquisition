"""Tests for FlyScanConfigurationService."""

import unittest
from datetime import datetime

from application.services.acquisition_configuration_service.flyscan_configuration_service import (
    FlyScanConfigurationService
)
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class TestFlyScanConfigurationService(unittest.TestCase):
    """Test suite for FlyScanConfigurationService."""

    def setUp(self):
        """Set up common fixtures."""
        self.service = FlyScanConfigurationService()
        self.scan_zone = ScanZone(x_min=0.0, x_max=100.0, y_min=0.0, y_max=100.0)

    def test_validate_compatible_config(self):
        """Test validation passes for compatible configuration."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(min_speed=1.0, target_speed=10.0, acceleration=5.0, deceleration=5.0),
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        capability = AcquisitionRateCapability(
            measured_rate_hz=150.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1500
        )

        result = self.service.validate_flyscan_config(config, capability)
        self.assertTrue(result.is_valid)

    def test_validate_incompatible_config(self):
        """Test validation fails for incompatible configuration."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(min_speed=1.0, target_speed=100.0, acceleration=50.0, deceleration=50.0),
            desired_acquisition_rate_hz=50.0,
            max_spatial_gap_mm=0.1
        )

        capability = AcquisitionRateCapability(
            measured_rate_hz=50.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=500
        )

        result = self.service.validate_flyscan_config(config, capability)
        self.assertFalse(result.is_valid)

    def test_suggest_compatible_profile_slows_down(self):
        """Test suggestion slows down incompatible profile."""
        fast_config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(min_speed=1.0, target_speed=50.0, acceleration=25.0, deceleration=25.0),
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        slow_capability = AcquisitionRateCapability(
            measured_rate_hz=50.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=500
        )

        suggested = self.service.suggest_compatible_motion_profile(fast_config, slow_capability)

        # Should be slower than original
        self.assertLess(suggested.target_speed, fast_config.motion_profile.target_speed)

    def test_estimate_flyscan_duration(self):
        """Test duration and point estimation."""
        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(min_speed=1.0, target_speed=5.0, acceleration=2.0, deceleration=2.0),
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1000
        )

        duration, points = self.service.estimate_flyscan_duration(config, capability)

        # Sanity checks
        self.assertGreater(duration, 0)
        self.assertGreater(points, 25)  # More than grid points


if __name__ == '__main__':
    unittest.main()
