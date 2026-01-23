"""
Unit tests for ScipySensorFrameCalibrationOptimizer.
"""

import unittest
from datetime import datetime
import numpy as np
from scipy.spatial.transform import Rotation as R

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from infrastructure.calibration.scipy_sensor_frame_calibration_optimizer import (
    ScipySensorFrameCalibrationOptimizer
)


class TestScipySensorFrameCalibrationOptimizer(unittest.TestCase):
    """Test suite for ScipySensorFrameCalibrationOptimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = ScipySensorFrameCalibrationOptimizer()
        self.timestamp = datetime.now()
    
    def test_voltage_to_vector(self):
        """Test conversion of VoltageMeasurement to 3D vector."""
        # Create a measurement with known values
        measurement = VoltageMeasurement(
            voltage_x_in_phase=3.0,
            voltage_x_quadrature=4.0,  # magnitude = 5.0
            voltage_y_in_phase=6.0,
            voltage_y_quadrature=8.0,  # magnitude = 10.0
            voltage_z_in_phase=5.0,
            voltage_z_quadrature=12.0,  # magnitude = 13.0
            timestamp=self.timestamp
        )
        
        vector = self.optimizer._voltage_to_vector(measurement)
        
        # Check magnitude calculations (sign preserved from in-phase component)
        self.assertAlmostEqual(vector[0], 5.0, places=6)  # sqrt(3² + 4²), sign from +3.0
        self.assertAlmostEqual(vector[1], 10.0, places=6)  # sqrt(6² + 8²), sign from +6.0
        self.assertAlmostEqual(vector[2], 13.0, places=6)  # sqrt(5² + 12²), sign from +5.0
    
    def test_voltage_to_vector_preserves_sign(self):
        """Test that voltage_to_vector preserves sign from in-phase component."""
        # Test with negative in-phase components
        measurement = VoltageMeasurement(
            voltage_x_in_phase=-3.0,
            voltage_x_quadrature=4.0,  # magnitude = 5.0
            voltage_y_in_phase=-6.0,
            voltage_y_quadrature=8.0,  # magnitude = 10.0
            voltage_z_in_phase=5.0,
            voltage_z_quadrature=12.0,  # magnitude = 13.0
            timestamp=self.timestamp
        )
        
        vector = self.optimizer._voltage_to_vector(measurement)
        
        # Check that sign is preserved
        self.assertAlmostEqual(vector[0], -5.0, places=6)  # negative sign preserved
        self.assertAlmostEqual(vector[1], -10.0, places=6)  # negative sign preserved
        self.assertAlmostEqual(vector[2], 13.0, places=6)  # positive sign preserved
    
    def test_residual_function_x_dir(self):
        """Test residual function for X_DIR excitation."""
        # Create measurement with X component only (ideal case)
        measurement = VoltageMeasurement(
            voltage_x_in_phase=10.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # With zero rotation, residuals should be zero (Y and Z components)
        angles = np.array([0.0, 0.0, 0.0])
        residuals = self.optimizer._residual_function(
            angles,
            [measurement],
            []
        )
        
        # Should have 2 residuals (Y and Z components)
        self.assertEqual(len(residuals), 2)
        self.assertAlmostEqual(residuals[0], 0.0, places=6)  # Y component
        self.assertAlmostEqual(residuals[1], 0.0, places=6)  # Z component
    
    def test_residual_function_y_dir(self):
        """Test residual function for Y_DIR excitation."""
        # Create measurement with Y component only (ideal case)
        measurement = VoltageMeasurement(
            voltage_x_in_phase=0.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=10.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # With zero rotation, residuals should be zero (X and Z components)
        angles = np.array([0.0, 0.0, 0.0])
        residuals = self.optimizer._residual_function(
            angles,
            [],
            [measurement]
        )
        
        # Should have 2 residuals (X and Z components)
        self.assertEqual(len(residuals), 2)
        self.assertAlmostEqual(residuals[0], 0.0, places=6)  # X component
        self.assertAlmostEqual(residuals[1], 0.0, places=6)  # Z component
    
    def test_residual_function_analytical_zero_case(self):
        """
        Test residual function with analytically known zero case.
        
        When the rotation angles are correct, the residuals should be exactly zero
        (within machine precision) for ideal measurements.
        This is a deterministic analytical test.
        """
        # Known rotation angles (in degrees)
        theta_x, theta_y, theta_z = 10.0, 15.0, 20.0
        known_angles = np.array([theta_x, theta_y, theta_z])
        rotation = R.from_euler('XYZ', known_angles, degrees=True)
        
        # Create ideal X_DIR excitation: E_bench = [E_0, 0, 0]
        E_0 = 10.0
        v_bench_x = np.array([E_0, 0.0, 0.0])
        
        # Analytically compute what the sensor would measure: E_probe = R_inv * E_bench
        # Using the formula from the documentation:
        # E_probe = R_z^-1 * R_y^-1 * R_x^-1 * E_bench
        # But since we're applying the rotation to go from bench to probe frame,
        # we use the inverse rotation
        v_probe_x = rotation.inv().apply(v_bench_x)
        
        x_measurement = VoltageMeasurement(
            voltage_x_in_phase=v_probe_x[0],
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=v_probe_x[1],
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=v_probe_x[2],
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Create ideal Y_DIR excitation: E_bench = [0, E_0, 0]
        v_bench_y = np.array([0.0, E_0, 0.0])
        v_probe_y = rotation.inv().apply(v_bench_y)
        
        y_measurement = VoltageMeasurement(
            voltage_x_in_phase=v_probe_y[0],
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=v_probe_y[1],
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=v_probe_y[2],
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Compute residuals with the CORRECT angles
        # Analytically, these should be exactly zero (within machine precision)
        residuals = self.optimizer._residual_function(
            known_angles,
            [x_measurement],
            [y_measurement]
        )
        
        # Verify residuals are zero (within machine precision for float64)
        # Expected: 4 residuals (2 for X_DIR: Y and Z, 2 for Y_DIR: X and Z)
        self.assertEqual(len(residuals), 4)
        for residual in residuals:
            self.assertAlmostEqual(residual, 0.0, places=10, 
                                 msg="Residuals should be exactly zero when angles are correct")
    
    def test_residual_function_analytical_formula_verification(self):
        """
        Test residual function using analytical rotation with 'XYZ' extrinsic convention.
        
        Uses 'XYZ' extrinsic rotations (matching TransformationService) to generate
        measurements analytically, then verifies the transformation.
        This is a deterministic analytical test.
        """
        # Test with specific angles
        theta_x, theta_y, theta_z = 0.0, 30.0, 45.0  # degrees
        angles = np.array([theta_x, theta_y, theta_z])
        
        E_0 = 10.0
        
        # For X_DIR excitation: E_bench = [E_0, 0, 0]
        # With 'XYZ' extrinsic: E_probe = R^-1 * E_bench (where R is extrinsic XYZ rotation)
        rotation = R.from_euler('XYZ', angles, degrees=True)
        v_bench_x = np.array([E_0, 0.0, 0.0])
        v_probe_x = rotation.inv().apply(v_bench_x)  # Analytically compute E_probe
        
        x_measurement = VoltageMeasurement(
            voltage_x_in_phase=v_probe_x[0],
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=v_probe_x[1],
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=v_probe_x[2],
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Compute residuals with correct angles
        residuals = self.optimizer._residual_function(
            angles,
            [x_measurement],
            []
        )
        
        # Analytically, when angles are correct, Y and Z components after transformation
        # should be zero. With 'XYZ' extrinsic: R transforms Sensor -> Source
        # So E_bench = R * E_probe (rotation directe)
        v_probe = self.optimizer._voltage_to_vector(x_measurement)
        v_transformed = rotation.apply(v_probe)  # Transform probe -> bench (sensor -> source)
        
        # Verify analytically: v_transformed should be [E_0, 0, 0]
        self.assertAlmostEqual(v_transformed[0], E_0, places=10)
        self.assertAlmostEqual(v_transformed[1], 0.0, places=10)
        self.assertAlmostEqual(v_transformed[2], 0.0, places=10)
        
        # Residuals should be zero (Y and Z components)
        self.assertEqual(len(residuals), 2)
        self.assertAlmostEqual(residuals[0], 0.0, places=10)
        self.assertAlmostEqual(residuals[1], 0.0, places=10)
    
    def test_optimize_angles_analytical_verification(self):
        """
        Test optimization with analytically computed measurements using 'XYZ' extrinsic rotations.
        
        Uses 'XYZ' extrinsic rotations (matching TransformationService and visualization code)
        to generate measurements analytically, then verifies that optimization recovers
        the exact angles (within numerical precision).
        This is a deterministic test based on analytical predictions.
        """
        # Known rotation angles (in degrees)
        known_angles = (10.0, 15.0, 20.0)
        theta_x, theta_y, theta_z = known_angles
        
        E_0 = 10.0
        
        # Create rotation using 'XYZ' extrinsic convention (matching TransformationService)
        rotation = R.from_euler('XYZ', known_angles, degrees=True)
        
        # For X_DIR excitation: E_bench = [E_0, 0, 0]
        # With 'XYZ' extrinsic: E_probe = R^-1 * E_bench
        v_bench_x = np.array([E_0, 0.0, 0.0])
        v_probe_x = rotation.inv().apply(v_bench_x)
        
        x_measurement = VoltageMeasurement(
            voltage_x_in_phase=v_probe_x[0],
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=v_probe_x[1],
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=v_probe_x[2],
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # For Y_DIR excitation: E_bench = [0, E_0, 0]
        v_bench_y = np.array([0.0, E_0, 0.0])
        v_probe_y = rotation.inv().apply(v_bench_y)
        
        y_measurement = VoltageMeasurement(
            voltage_x_in_phase=v_probe_y[0],
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=v_probe_y[1],
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=v_probe_y[2],
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Optimize starting from zero angles
        optimized = self.optimizer.optimize_angles(
            [x_measurement],
            [y_measurement],
            initial_angles=(0.0, 0.0, 0.0)
        )
        
        # Verify optimized angles match known angles (within numerical precision of optimization)
        # The optimization should converge to the exact analytical solution
        self.assertAlmostEqual(optimized[0], known_angles[0], places=3,
                             msg="theta_x should match analytically")
        self.assertAlmostEqual(optimized[1], known_angles[1], places=3,
                             msg="theta_y should match analytically")
        self.assertAlmostEqual(optimized[2], known_angles[2], places=3,
                             msg="theta_z should match analytically")
    
    def test_optimize_angles_empty_measurements(self):
        """Test that empty measurement lists raise an error."""
        with self.assertRaises(ValueError):
            self.optimizer.optimize_angles([], [])


if __name__ == '__main__':
    unittest.main()
