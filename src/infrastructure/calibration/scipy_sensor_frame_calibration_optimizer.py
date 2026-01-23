"""
Infrastructure Adapter: Scipy Sensor Frame Calibration Optimizer

Implements sensor frame calibration angle optimization using scipy.optimize.least_squares.
"""

from typing import List, Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.optimize import least_squares

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.services.sensor_frame_autocalibration_service.i_sensor_frame_calibration_optimizer import (
    ISensorFrameCalibrationOptimizer
)


class ScipySensorFrameCalibrationOptimizer(ISensorFrameCalibrationOptimizer):
    """
    Infrastructure adapter for optimizing sensor frame rotation angles using scipy.
    
    Uses least squares optimization to find angles that minimize unwanted components:
    - X_DIR excitation: minimize Y and Z components after transformation
    - Y_DIR excitation: minimize X and Z components after transformation
    """
    
    def optimize_angles(
        self,
        x_measurements: List[VoltageMeasurement],
        y_measurements: List[VoltageMeasurement],
        initial_angles: Optional[Tuple[float, float, float]] = None
    ) -> Tuple[float, float, float]:
        """
        Optimize sensor frame rotation angles using least squares.
        
        Args:
            x_measurements: Measurements with X_DIR excitation
            y_measurements: Measurements with Y_DIR excitation
            initial_angles: Optional initial guess (theta_x, theta_y, theta_z) in degrees
        
        Returns:
            Optimized angles (theta_x, theta_y, theta_z) in degrees
        """
        if not x_measurements and not y_measurements:
            raise ValueError("At least one measurement list must be non-empty")
        
        # Default initial guess: all zeros
        if initial_angles is None:
            initial_angles = (0.0, 0.0, 0.0)
        
        initial_angles_array = np.array(initial_angles, dtype=float)
        
        # Optimize using least squares
        result = least_squares(
            self._residual_function,
            initial_angles_array,
            args=(x_measurements, y_measurements),
            method='lm',  # Levenberg-Marquardt algorithm
            ftol=1e-6,
            xtol=1e-6,
            gtol=1e-6
        )
        
        if not result.success:
            raise RuntimeError(f"Optimization failed: {result.message}")
        
        optimized_angles = tuple(result.x)
        return optimized_angles
    
    def _voltage_to_vector(self, measurement: VoltageMeasurement) -> np.ndarray:
        """
        Convert voltage measurement to 3D vector using complex magnitude.
        No gain conversion needed (proportional factor).
        
        Uses the complex magnitude sqrt(I² + Q²) to get the amplitude.
        Note: This preserves the sign information through the in-phase component
        when quadrature is zero (which is the case for ideal measurements).
        
        Args:
            measurement: VoltageMeasurement to convert
        
        Returns:
            3D numpy array [v_x, v_y, v_z] with complex magnitude
        """
        # For calibration, we want to maximize the amplitude in the expected direction
        # The magnitude sqrt(I² + Q²) gives the amplitude, but we need to preserve
        # the sign information. Since we're maximizing alignment, we use the in-phase
        # component sign combined with the magnitude.
        v_x_mag = np.sqrt(measurement.voltage_x_in_phase**2 + measurement.voltage_x_quadrature**2)
        v_y_mag = np.sqrt(measurement.voltage_y_in_phase**2 + measurement.voltage_y_quadrature**2)
        v_z_mag = np.sqrt(measurement.voltage_z_in_phase**2 + measurement.voltage_z_quadrature**2)
        
        # Preserve sign from in-phase component
        v_x = v_x_mag if measurement.voltage_x_in_phase >= 0 else -v_x_mag
        v_y = v_y_mag if measurement.voltage_y_in_phase >= 0 else -v_y_mag
        v_z = v_z_mag if measurement.voltage_z_in_phase >= 0 else -v_z_mag
        
        return np.array([v_x, v_y, v_z])
    
    def _residual_function(
        self,
        angles: np.ndarray,
        x_measurements: List[VoltageMeasurement],
        y_measurements: List[VoltageMeasurement]
    ) -> np.ndarray:
        """
        Compute residuals for least squares optimization.
        
        Objective:
        - X_DIR excitation: minimize Y and Z components after transformation
        - Y_DIR excitation: minimize X and Z components after transformation
        
        Args:
            angles: Rotation angles [theta_x, theta_y, theta_z] in degrees
            x_measurements: Measurements with X_DIR excitation
            y_measurements: Measurements with Y_DIR excitation
        
        Returns:
            Array of residuals to minimize
        """
        theta_x, theta_y, theta_z = angles
        # Use 'XYZ' (extrinsic) to match TransformationService convention
        # Rotations around fixed axes (extrinsic rotations)
        rotation = R.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)
        
        residuals = []
        
        # For X_DIR: minimize Y and Z components after transformation
        # With 'XYZ' extrinsic: R transforms Sensor -> Source (bench)
        # So E_bench = R * E_probe (rotation directe, comme transform_sensor_to_source)
        for meas in x_measurements:
            v_probe = self._voltage_to_vector(meas)
            v_bench = rotation.apply(v_probe)  # Transform probe -> bench (sensor -> source)
            residuals.append(v_bench[1])  # Y component (should be 0)
            residuals.append(v_bench[2])  # Z component (should be 0)
        
        # For Y_DIR: minimize X and Z components after transformation
        for meas in y_measurements:
            v_probe = self._voltage_to_vector(meas)
            v_bench = rotation.apply(v_probe)  # Transform probe -> bench (sensor -> source)
            residuals.append(v_bench[0])  # X component (should be 0)
            residuals.append(v_bench[2])  # Z component (should be 0)
        
        return np.array(residuals)
