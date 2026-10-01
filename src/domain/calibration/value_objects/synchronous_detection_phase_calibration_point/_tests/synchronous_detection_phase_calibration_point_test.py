import unittest

from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)


class TestSynchronousDetectionPhaseCalibrationPoint(unittest.TestCase):
    def test_creates_with_positive_frequency_and_positive_delta(self):
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=12.5)
        self.assertEqual(point.frequency_hz, 1000.0)
        self.assertEqual(point.delta_phi_degrees, 12.5)

    def test_allows_negative_delta_phi(self):
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=-45.0)
        self.assertEqual(point.delta_phi_degrees, -45.0)

    def test_is_immutable(self):
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=0.0)
        with self.assertRaises(Exception):
            point.frequency_hz = 2000.0

    def test_rejects_zero_frequency(self):
        with self.assertRaises(ValueError):
            SynchronousDetectionPhaseCalibrationPoint(frequency_hz=0.0, delta_phi_degrees=0.0)

    def test_rejects_negative_frequency(self):
        with self.assertRaises(ValueError):
            SynchronousDetectionPhaseCalibrationPoint(frequency_hz=-100.0, delta_phi_degrees=0.0)


if __name__ == "__main__":
    unittest.main()
