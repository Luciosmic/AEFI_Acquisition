"""Tests for AcquisitionRateMeasurementService."""

import unittest
from datetime import datetime

from application.services.acquisition_configuration_service.acquisition_rate_measurement_service import (
    AcquisitionRateMeasurementService
)
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class MockAcquisitionPort:
    """Mock acquisition port for testing."""

    def __init__(self, sample_delay_s: float = 0.01):
        self.sample_delay_s = sample_delay_s
        self.sample_count = 0

    def acquire_sample(self) -> VoltageMeasurement:
        import time
        time.sleep(self.sample_delay_s)
        self.sample_count += 1
        return VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )

    def is_ready(self) -> bool:
        return True


class TestAcquisitionRateMeasurementService(unittest.TestCase):
    """Test suite for AcquisitionRateMeasurementService."""

    def test_measure_acquisition_rate(self):
        """Test measuring acquisition rate."""
        service = AcquisitionRateMeasurementService()
        mock_port = MockAcquisitionPort(sample_delay_s=0.01)  # ~100 Hz

        capability = service.measure_acquisition_rate(
            mock_port,
            measurement_duration_s=1.0,
            warmup_samples=5
        )

        # Should measure ~100 Hz
        self.assertGreater(capability.measured_rate_hz, 50)
        self.assertLess(capability.measured_rate_hz, 150)
        self.assertGreater(capability.sample_count, 50)

    def test_caching_works(self):
        """Test that caching avoids re-measurement."""
        service = AcquisitionRateMeasurementService()
        mock_port = MockAcquisitionPort(sample_delay_s=0.01)

        # First measurement
        capability1 = service.measure_acquisition_rate(mock_port, measurement_duration_s=0.5)

        # Get cached
        cached = service.get_cached_capability()
        self.assertIsNotNone(cached)
        self.assertEqual(cached.measured_rate_hz, capability1.measured_rate_hz)

    def test_measure_or_use_cached(self):
        """Test measure_or_use_cached uses cache."""
        service = AcquisitionRateMeasurementService()
        mock_port = MockAcquisitionPort(sample_delay_s=0.01)

        # First call measures
        capability1 = service.measure_or_use_cached(mock_port)
        count1 = mock_port.sample_count

        # Second call uses cache
        capability2 = service.measure_or_use_cached(mock_port)
        count2 = mock_port.sample_count

        # Should be same capability
        self.assertEqual(capability1.measured_rate_hz, capability2.measured_rate_hz)
        # Should not have acquired more samples
        self.assertEqual(count1, count2)

    def test_force_remeasure(self):
        """Test force_remeasure bypasses cache."""
        service = AcquisitionRateMeasurementService()
        mock_port = MockAcquisitionPort(sample_delay_s=0.01)

        capability1 = service.measure_or_use_cached(mock_port)
        count1 = mock_port.sample_count

        # Force remeasure
        capability2 = service.measure_or_use_cached(mock_port, force_remeasure=True)
        count2 = mock_port.sample_count

        # Should have acquired more samples
        self.assertGreater(count2, count1)


if __name__ == '__main__':
    unittest.main()
