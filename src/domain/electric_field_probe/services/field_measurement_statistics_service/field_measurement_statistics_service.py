"""
Domain Service: Field Measurement Statistics

Responsibility:
    Calculate statistical properties (mean, std dev) of a set of electric field measurements.

Rationale:
    Provides domain-level statistics calculation for FieldMeasurement value objects,
    enabling averaging and uncertainty estimation during scan operations.
    
Design:
    - Static service (no internal state)
    - Operates on immutable FieldMeasurement value objects
    - Returns a new FieldMeasurement with averaged components and computed standard deviations
    - Validates that all measurements have consistent component counts
"""

from typing import List
import math
from datetime import datetime
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement


class FieldMeasurementStatisticsService:
    """
    Domain Service for calculating statistics on electric field measurements.
    """
    
    @staticmethod
    def calculate_statistics(measurements: List[FieldMeasurement]) -> FieldMeasurement:
        """
        Calculate the mean and standard deviation of a list of field measurements.
        
        Args:
            measurements: List of FieldMeasurement objects.
            
        Returns:
            A new FieldMeasurement object containing the mean values and 
            populated standard deviation fields.
            
        Raises:
            ValueError: If the list is empty or measurements have inconsistent dimensions.
        """
        if not measurements:
            raise ValueError("Cannot calculate statistics on empty measurement list")
        
        # Validate all measurements have the same dimensionality
        n_components = len(measurements[0].components)
        for i, m in enumerate(measurements):
            if len(m.components) != n_components:
                raise ValueError(
                    f"All measurements must have the same number of components. "
                    f"Expected {n_components}, got {len(m.components)} at index {i}"
                )
        
        n = len(measurements)
        
        if n == 1:
            # If only one measurement, mean is the value, std dev is 0
            m = measurements[0]
            return FieldMeasurement(
                components=m.components,
                timestamp=m.timestamp,
                uncertainty_estimate=m.uncertainty_estimate,
                std_dev_components=tuple(0.0 for _ in m.components)
            )
        
        # Initialize sums for mean calculation
        sum_components = [0.0] * n_components
        
        for m in measurements:
            for i, value in enumerate(m.components):
                sum_components[i] += value
        
        # Calculate Means
        mean_components = [s / n for s in sum_components]
        
        # Calculate Variance Sums
        var_sums = [0.0] * n_components
        
        for m in measurements:
            for i, value in enumerate(m.components):
                diff = value - mean_components[i]
                var_sums[i] += diff ** 2
        
        # Calculate Std Dev (Sample Standard Deviation, divide by n-1)
        # If n > 1, use n-1 (Bessel's correction).
        divisor = n - 1
        std_dev_components = [math.sqrt(vs / divisor) for vs in var_sums]
        
        # Use the timestamp of the last measurement
        last_timestamp = measurements[-1].timestamp
        
        # Calculate combined uncertainty (optional enhancement)
        # For now, just pass through the first measurement's uncertainty or None
        uncertainty_estimate = measurements[0].uncertainty_estimate
        
        return FieldMeasurement(
            components=tuple(mean_components),
            timestamp=last_timestamp,
            uncertainty_estimate=uncertainty_estimate,
            std_dev_components=tuple(std_dev_components)
        )
