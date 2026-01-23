"""
Port Interface: Sensor Frame Calibration Optimizer

Defines the interface for optimizing sensor frame rotation angles.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class ISensorFrameCalibrationOptimizer(ABC):
    """Port interface for sensor frame calibration angle optimization."""
    
    @abstractmethod
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
        pass
