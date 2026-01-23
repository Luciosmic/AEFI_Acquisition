"""
Unit tests for SensorFrameAutocalibrationService.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.services.transformation_service.transformation_service import TransformationService
from application.services.sensor_frame_autocalibration_service.sensor_frame_autocalibration_service import (
    SensorFrameAutocalibrationService
)
from application.services.sensor_frame_autocalibration_service.i_sensor_frame_calibration_optimizer import (
    ISensorFrameCalibrationOptimizer
)


class MockOptimizer(ISensorFrameCalibrationOptimizer):
    """Mock optimizer for testing."""
    
    def __init__(self, return_angles=(0.0, 0.0, 0.0)):
        self.return_angles = return_angles
        self.called_with = None
    
    def optimize_angles(self, x_measurements, y_measurements, initial_angles=None):
        self.called_with = {
            'x_measurements': x_measurements,
            'y_measurements': y_measurements,
            'initial_angles': initial_angles
        }
        return self.return_angles


class TestSensorFrameAutocalibrationService(unittest.TestCase):
    """Test suite for SensorFrameAutocalibrationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transformation_service = TransformationService()
        self.optimizer = MockOptimizer(return_angles=(10.0, 15.0, 20.0))
        self.service = SensorFrameAutocalibrationService(
            transformation_service=self.transformation_service,
            optimizer=self.optimizer
        )
        self.timestamp = datetime.now()
    
    def test_calibrate_from_measurements_calls_optimizer(self):
        """Test that calibration delegates to optimizer."""
        x_measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=10.0,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
        ]
        y_measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=0.0,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=10.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
        ]
        
        result = self.service.calibrate_from_measurements(
            x_measurements,
            y_measurements
        )
        
        # Verify optimizer was called with correct parameters
        self.assertIsNotNone(self.optimizer.called_with)
        self.assertEqual(self.optimizer.called_with['x_measurements'], x_measurements)
        self.assertEqual(self.optimizer.called_with['y_measurements'], y_measurements)
        self.assertIsNone(self.optimizer.called_with['initial_angles'])
        
        # Verify result matches optimizer return value
        self.assertEqual(result, (10.0, 15.0, 20.0))
    
    def test_calibrate_from_measurements_updates_transformation_service(self):
        """Test that calibration updates the transformation service."""
        x_measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=10.0,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
        ]
        y_measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=0.0,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=10.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
        ]
        
        # Verify initial angles are zero
        initial_angles = self.transformation_service.get_rotation_angles()
        self.assertEqual(initial_angles, (0.0, 0.0, 0.0))
        
        # Calibrate
        self.service.calibrate_from_measurements(x_measurements, y_measurements)
        
        # Verify transformation service was updated
        updated_angles = self.transformation_service.get_rotation_angles()
        self.assertEqual(updated_angles, (10.0, 15.0, 20.0))
    
    def test_calibrate_from_measurements_with_initial_angles(self):
        """Test that initial angles are passed to optimizer."""
        x_measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=10.0,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
        ]
        y_measurements = []
        initial_angles = (5.0, 10.0, 15.0)
        
        self.service.calibrate_from_measurements(
            x_measurements,
            y_measurements,
            initial_angles=initial_angles
        )
        
        # Verify initial angles were passed to optimizer
        self.assertEqual(self.optimizer.called_with['initial_angles'], initial_angles)


if __name__ == '__main__':
    unittest.main()
