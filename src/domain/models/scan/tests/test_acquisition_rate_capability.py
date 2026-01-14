"""
Unit Tests for AcquisitionRateCapability Value Object

Tests the measured acquisition rate capability and its validation logic.
"""

import unittest
from datetime import datetime, timedelta

from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability


class TestAcquisitionRateCapability(unittest.TestCase):
    """Test suite for AcquisitionRateCapability value object."""

    def test_create_valid_capability(self):
        """Test creating a valid capability measurement."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1000,
            configuration_hash="abc123"
        )

        self.assertEqual(capability.measured_rate_hz, 100.0)
        self.assertEqual(capability.measured_std_dev_hz, 5.0)
        self.assertEqual(capability.sample_count, 1000)

    def test_invalid_rate_rejected(self):
        """Test that zero or negative rates are rejected."""
        with self.assertRaises(ValueError) as ctx:
            AcquisitionRateCapability(
                measured_rate_hz=0.0,  # Invalid
                measured_std_dev_hz=5.0,
                measurement_timestamp=datetime.now(),
                measurement_duration_s=10.0,
                sample_count=100
            )
        self.assertIn("positive", str(ctx.exception).lower())

        with self.assertRaises(ValueError):
            AcquisitionRateCapability(
                measured_rate_hz=-10.0,  # Invalid
                measured_std_dev_hz=5.0,
                measurement_timestamp=datetime.now(),
                measurement_duration_s=10.0,
                sample_count=100
            )

    def test_invalid_std_dev_rejected(self):
        """Test that negative std_dev is rejected."""
        with self.assertRaises(ValueError):
            AcquisitionRateCapability(
                measured_rate_hz=100.0,
                measured_std_dev_hz=-1.0,  # Invalid
                measurement_timestamp=datetime.now(),
                measurement_duration_s=10.0,
                sample_count=100
            )

    def test_insufficient_samples_rejected(self):
        """Test that < 10 samples is rejected."""
        with self.assertRaises(ValueError) as ctx:
            AcquisitionRateCapability(
                measured_rate_hz=100.0,
                measured_std_dev_hz=5.0,
                measurement_timestamp=datetime.now(),
                measurement_duration_s=10.0,
                sample_count=5  # Too few
            )
        self.assertIn("10 samples", str(ctx.exception).lower())

    def test_coefficient_of_variation(self):
        """Test CV calculation."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )

        cv = capability.get_coefficient_of_variation()
        self.assertAlmostEqual(cv, 5.0, places=2)  # 5/100 * 100 = 5%

    def test_is_stable_for_flyscan(self):
        """Test stability check for FlyScan."""
        # Stable capability (CV = 2%)
        stable = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=2.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )
        self.assertTrue(stable.is_stable_for_flyscan(max_cv_percent=5.0))

        # Unstable capability (CV = 10%)
        unstable = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=10.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )
        self.assertFalse(unstable.is_stable_for_flyscan(max_cv_percent=5.0))

    def test_minimum_guaranteed_rate(self):
        """Test minimum guaranteed rate calculation."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )

        # 3-sigma guarantee: 100 - 3*5 = 85 Hz
        min_rate = capability.get_minimum_guaranteed_rate_hz(confidence_sigma=3.0)
        self.assertAlmostEqual(min_rate, 85.0, places=2)

        # 1-sigma guarantee: 100 - 1*5 = 95 Hz
        min_rate = capability.get_minimum_guaranteed_rate_hz(confidence_sigma=1.0)
        self.assertAlmostEqual(min_rate, 95.0, places=2)

    def test_minimum_guaranteed_rate_cannot_be_negative(self):
        """Test that minimum rate is clamped at 0."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=10.0,
            measured_std_dev_hz=20.0,  # Very high uncertainty
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )

        # 3-sigma: 10 - 3*20 = -50, should clamp to 0
        min_rate = capability.get_minimum_guaranteed_rate_hz(confidence_sigma=3.0)
        self.assertEqual(min_rate, 0.0)

    def test_maximum_spacing_for_motion(self):
        """Test spatial gap calculation."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )

        # At 10 mm/s with 85 Hz (3-sigma min): gap = 10/85 ≈ 0.118 mm
        max_spacing = capability.get_maximum_spacing_for_motion(
            motion_speed_mm_s=10.0,
            confidence_sigma=3.0
        )
        self.assertAlmostEqual(max_spacing, 10.0 / 85.0, places=3)

    def test_is_measurement_recent(self):
        """Test recency check."""
        # Recent measurement
        recent = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=100
        )
        self.assertTrue(recent.is_measurement_recent(max_age_seconds=300))

        # Stale measurement
        stale = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now() - timedelta(seconds=400),
            measurement_duration_s=10.0,
            sample_count=100
        )
        self.assertFalse(stale.is_measurement_recent(max_age_seconds=300))

    def test_str_representation(self):
        """Test string representation."""
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=10.0,
            sample_count=1000
        )

        str_repr = str(capability)
        self.assertIn("100.0", str_repr)
        self.assertIn("5.0", str_repr)
        self.assertIn("Hz", str_repr)
        self.assertIn("1000", str_repr)


if __name__ == '__main__':
    unittest.main()
