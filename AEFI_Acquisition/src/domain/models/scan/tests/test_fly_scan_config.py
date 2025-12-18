"""
Unit Tests for FlyScanConfig Value Object

Tests FlyScan configuration and validation against acquisition capabilities.
"""

import unittest
from datetime import datetime

from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class TestFlyScanConfig(unittest.TestCase):
    """Test suite for FlyScanConfig value object."""

    def setUp(self):
        """Set up common test fixtures."""
        self.scan_zone = ScanZone(x_min=0.0, x_max=100.0, y_min=0.0, y_max=100.0)
        self.motion_profile = MotionProfile(
            min_speed=1.0,
            target_speed=10.0,
            acceleration=5.0,
            deceleration=5.0
        )

    def test_create_valid_config(self):
        """Test creating a valid FlyScan configuration."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        self.assertEqual(config.x_nb_points, 10)
        self.assertEqual(config.desired_acquisition_rate_hz, 100.0)
        self.assertEqual(config.max_spatial_gap_mm, 0.5)

    def test_invalid_grid_size_rejected(self):
        """Test that grid size < 2 is rejected."""
        with self.assertRaises(ValueError):
            FlyScanConfig(
                scan_zone=self.scan_zone,
                x_nb_points=1,  # Too small
                y_nb_points=10,
                scan_pattern=ScanPattern.SERPENTINE,
                motion_profile=self.motion_profile,
                desired_acquisition_rate_hz=100.0
            )

    def test_invalid_acquisition_rate_rejected(self):
        """Test that zero or negative acquisition rate is rejected."""
        with self.assertRaises(ValueError):
            FlyScanConfig(
                scan_zone=self.scan_zone,
                x_nb_points=10,
                y_nb_points=10,
                scan_pattern=ScanPattern.SERPENTINE,
                motion_profile=self.motion_profile,
                desired_acquisition_rate_hz=0.0  # Invalid
            )

    def test_calculate_required_minimum_rate(self):
        """Test calculation of minimum required rate."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        # Required rate = target_speed / max_gap = 10 / 0.5 = 20 Hz
        required_rate = config.calculate_required_minimum_rate_hz()
        self.assertAlmostEqual(required_rate, 20.0, places=2)

    def test_validate_compatible_configuration(self):
        """Test validation passes for compatible config."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        # Create compatible capability
        capability = AcquisitionRateCapability(
            measured_rate_hz=150.0,  # Higher than desired
            measured_std_dev_hz=5.0,  # Low variance (stable)
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1500
        )

        result = config.validate_with_capability(capability)
        self.assertTrue(result.is_valid)

    def test_validate_insufficient_rate_rejected(self):
        """Test validation fails when hardware is too slow."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=1.0,
                target_speed=100.0,  # Very fast motion
                acceleration=50.0,
                deceleration=50.0
            ),
            desired_acquisition_rate_hz=50.0,
            max_spatial_gap_mm=0.1  # Very tight tolerance
        )

        # Create slow capability
        # Required: 100mm/s / 0.1mm = 1000 Hz
        # Capability: ~40 Hz (guaranteed at 3-sigma)
        capability = AcquisitionRateCapability(
            measured_rate_hz=50.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=500
        )

        result = config.validate_with_capability(capability)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("cannot achieve required", result.errors[0].lower())

    def test_validate_desired_rate_too_high(self):
        """Test validation fails when desired rate exceeds measured."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=200.0,  # Wants 200 Hz
            max_spatial_gap_mm=1.0
        )

        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,  # Can only do 100 Hz
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1000
        )

        result = config.validate_with_capability(capability)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("desired acquisition rate", result.errors[0].lower())

    def test_validate_unstable_rate_warning(self):
        """Test validation warns for unstable acquisition rate."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.5
        )

        # Create unstable capability (CV > 5%)
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=15.0,  # High variance (CV = 15%)
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1000
        )

        result = config.validate_with_capability(capability)
        # Should be valid but with warnings
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("unstable", result.warnings[0].lower())

    def test_estimate_total_points(self):
        """Test estimation of total acquisition points."""
        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=1.0,
                target_speed=5.0,
                acceleration=2.0,
                deceleration=2.0
            ),
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

        total_points = config.estimate_total_points(capability)

        # Should be significantly more than grid points (25)
        self.assertGreater(total_points, 25)

        # Rough sanity check: distance ~50-90mm, speed ~3mm/s, duration ~20s, rate 100Hz
        # Should be in ballpark of 2000 points
        self.assertLess(total_points, 10000)  # Not astronomical

    def test_total_grid_points(self):
        """Test total grid points calculation."""
        config = FlyScanConfig(
            scan_zone=self.scan_zone,
            x_nb_points=10,
            y_nb_points=5,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=self.motion_profile,
            desired_acquisition_rate_hz=100.0
        )

        self.assertEqual(config.total_grid_points(), 50)


if __name__ == '__main__':
    unittest.main()
