"""
Domain: Signal Calibration Service

Responsibility:
    Pure domain logic for calculating calibration parameters from measurements.

Rationale:
    - Encapsulates calculation logic (atan2 for phase angles)
    - Pure function, no side effects
    - Reusable across application services

Design:
    - Static methods (no state)
    - Pure domain logic
"""
from typing import Dict
import math
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class SignalCalibrationService:
    """
    Service for calculating signal calibration parameters.
    
    Pure domain logic with no side effects.
    """
    
    @staticmethod
    def calculate_phase_angles(measurement: VoltageMeasurement) -> Dict[str, float]:
        """
        Calculate phase angles to align (I, Q) onto the I axis.
        
        For each axis, calculates atan2(Q, I) to determine the rotation angle
        needed to align the vector onto the I axis (Q=0).
        
        Args:
            measurement: VoltageMeasurement to analyze
        
        Returns:
            Dict with keys 'x', 'y', 'z' and values in radians
        """
        angles = {}
        
        for axis in ['x', 'y', 'z']:
            i_val, q_val = measurement._get_axis_values(axis)
            # Calculate angle to rotate (I, Q) onto I axis
            theta = math.atan2(q_val, i_val)
            angles[axis] = theta
        
        return angles
