"""
Domain Service: Measurement Statistics
Responsibility: Calculate statistical properties (mean, std dev) of a set of measurements.
"""

from typing import List
import math
from datetime import datetime
from domain.model.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement

class MeasurementStatisticsService:
    """
    Domain Service for calculating statistics on measurements.
    """
    
    @staticmethod
    def calculate_statistics(measurements: List[VoltageMeasurement]) -> VoltageMeasurement:
        """
        Calculate the mean and standard deviation of a list of measurements.
        
        Args:
            measurements: List of VoltageMeasurement objects.
            
        Returns:
            A new VoltageMeasurement object containing the mean values and 
            populated standard deviation fields.
            
        Raises:
            ValueError: If the list is empty.
        """
        if not measurements:
            raise ValueError("Cannot calculate statistics on empty measurement list")
            
        n = len(measurements)
        if n == 1:
            # If only one measurement, mean is the value, std dev is 0 (or undefined/None?)
            # Let's set it to 0.0 for consistency if we are doing "averaging" of 1 point.
            m = measurements[0]
            return VoltageMeasurement(
                voltage_x_in_phase=m.voltage_x_in_phase,
                voltage_x_quadrature=m.voltage_x_quadrature,
                voltage_y_in_phase=m.voltage_y_in_phase,
                voltage_y_quadrature=m.voltage_y_quadrature,
                voltage_z_in_phase=m.voltage_z_in_phase,
                voltage_z_quadrature=m.voltage_z_quadrature,
                timestamp=m.timestamp,
                uncertainty_estimate_volts=m.uncertainty_estimate_volts,
                std_dev_x_in_phase=0.0,
                std_dev_x_quadrature=0.0,
                std_dev_y_in_phase=0.0,
                std_dev_y_quadrature=0.0,
                std_dev_z_in_phase=0.0,
                std_dev_z_quadrature=0.0
            )
            
        # Initialize sums
        sum_x_i = 0.0
        sum_x_q = 0.0
        sum_y_i = 0.0
        sum_y_q = 0.0
        sum_z_i = 0.0
        sum_z_q = 0.0
        
        for m in measurements:
            sum_x_i += m.voltage_x_in_phase
            sum_x_q += m.voltage_x_quadrature
            sum_y_i += m.voltage_y_in_phase
            sum_y_q += m.voltage_y_quadrature
            sum_z_i += m.voltage_z_in_phase
            sum_z_q += m.voltage_z_quadrature
            
        # Calculate Means
        mean_x_i = sum_x_i / n
        mean_x_q = sum_x_q / n
        mean_y_i = sum_y_i / n
        mean_y_q = sum_y_q / n
        mean_z_i = sum_z_i / n
        mean_z_q = sum_z_q / n
        
        # Calculate Variance Sums
        var_sum_x_i = 0.0
        var_sum_x_q = 0.0
        var_sum_y_i = 0.0
        var_sum_y_q = 0.0
        var_sum_z_i = 0.0
        var_sum_z_q = 0.0
        
        for m in measurements:
            var_sum_x_i += (m.voltage_x_in_phase - mean_x_i) ** 2
            var_sum_x_q += (m.voltage_x_quadrature - mean_x_q) ** 2
            var_sum_y_i += (m.voltage_y_in_phase - mean_y_i) ** 2
            var_sum_y_q += (m.voltage_y_quadrature - mean_y_q) ** 2
            var_sum_z_i += (m.voltage_z_in_phase - mean_z_i) ** 2
            var_sum_z_q += (m.voltage_z_quadrature - mean_z_q) ** 2
            
        # Calculate Std Dev (Sample Standard Deviation, divide by n-1)
        # If n > 1, use n-1 (Bessel's correction).
        divisor = n - 1
        
        std_x_i = math.sqrt(var_sum_x_i / divisor)
        std_x_q = math.sqrt(var_sum_x_q / divisor)
        std_y_i = math.sqrt(var_sum_y_i / divisor)
        std_y_q = math.sqrt(var_sum_y_q / divisor)
        std_z_i = math.sqrt(var_sum_z_i / divisor)
        std_z_q = math.sqrt(var_sum_z_q / divisor)
        
        # Use the timestamp of the last measurement or average? 
        # Usually last or first. Let's use the last one to indicate when the averaging completed.
        last_timestamp = measurements[-1].timestamp
        
        return VoltageMeasurement(
            voltage_x_in_phase=mean_x_i,
            voltage_x_quadrature=mean_x_q,
            voltage_y_in_phase=mean_y_i,
            voltage_y_quadrature=mean_y_q,
            voltage_z_in_phase=mean_z_i,
            voltage_z_quadrature=mean_z_q,
            timestamp=last_timestamp,
            uncertainty_estimate_volts=None, # Or calculate combined uncertainty?
            std_dev_x_in_phase=std_x_i,
            std_dev_x_quadrature=std_x_q,
            std_dev_y_in_phase=std_y_i,
            std_dev_y_quadrature=std_y_q,
            std_dev_z_in_phase=std_z_i,
            std_dev_z_quadrature=std_z_q
        )
