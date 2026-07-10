"""
Tests for FieldMeasurementStatisticsService
"""

from datetime import datetime
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.electric_field_probe.services.field_measurement_statistics_service.field_measurement_statistics_service import FieldMeasurementStatisticsService


class TestFieldMeasurementStatisticsService:
    """Tests for FieldMeasurementStatisticsService."""
    
    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        try:
            FieldMeasurementStatisticsService.calculate_statistics([])
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "empty" in str(e).lower()
    
    def test_single_measurement(self):
        """Test statistics with a single measurement."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        measurement = FieldMeasurement(
            components=(1.0, 2.0, 3.0),
            timestamp=timestamp,
            uncertainty_estimate=0.1
        )
        
        result = FieldMeasurementStatisticsService.calculate_statistics([measurement])
        
        assert result.components == (1.0, 2.0, 3.0)
        assert result.timestamp == timestamp
        assert result.uncertainty_estimate == 0.1
        assert result.std_dev_components == (0.0, 0.0, 0.0)
    
    def test_two_measurements(self):
        """Test statistics with two measurements."""
        timestamp1 = datetime(2024, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2024, 1, 1, 12, 0, 1)
        
        m1 = FieldMeasurement(
            components=(1.0, 2.0, 3.0),
            timestamp=timestamp1,
            uncertainty_estimate=0.1
        )
        m2 = FieldMeasurement(
            components=(3.0, 4.0, 5.0),
            timestamp=timestamp2,
            uncertainty_estimate=0.2
        )
        
        result = FieldMeasurementStatisticsService.calculate_statistics([m1, m2])
        
        # Mean should be (2.0, 3.0, 4.0)
        assert result.components == (2.0, 3.0, 4.0)
        assert result.timestamp == timestamp2
        assert result.uncertainty_estimate == 0.1  # From first measurement
        
        # Std dev: for two points with values (1,3) mean=2, variance = ((1-2)^2 + (3-2)^2)/(2-1) = (1+1)/1 = 2, std_dev = sqrt(2)
        import math
        assert math.isclose(result.std_dev_components[0], math.sqrt(2), rel_tol=1e-9)
        assert math.isclose(result.std_dev_components[1], math.sqrt(2), rel_tol=1e-9)
        assert math.isclose(result.std_dev_components[2], math.sqrt(2), rel_tol=1e-9)
    
    def test_inconsistent_dimensions_raises_error(self):
        """Test that measurements with different dimensions raise ValueError."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        m1 = FieldMeasurement(components=(1.0, 2.0), timestamp=timestamp)
        m2 = FieldMeasurement(components=(1.0, 2.0, 3.0), timestamp=timestamp)
        
        try:
            FieldMeasurementStatisticsService.calculate_statistics([m1, m2])
            assert False, "Expected ValueError for inconsistent dimensions"
        except ValueError as e:
            assert "dimension" in str(e).lower() or "component" in str(e).lower()
    
    def test_three_measurements_mono_axial(self):
        """Test with three mono-axial measurements."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        m1 = FieldMeasurement(components=(1.0,), timestamp=timestamp)
        m2 = FieldMeasurement(components=(2.0,), timestamp=timestamp)
        m3 = FieldMeasurement(components=(3.0,), timestamp=timestamp)
        
        result = FieldMeasurementStatisticsService.calculate_statistics([m1, m2, m3])
        
        # Mean = 2.0
        assert result.components == (2.0,)
        
        # Variance = ((1-2)^2 + (2-2)^2 + (3-2)^2) / (3-1) = (1 + 0 + 1) / 2 = 1
        # Std dev = sqrt(1) = 1.0
        assert result.std_dev_components == (1.0,)
    
    def test_norm_property(self):
        """Test that norm is calculated correctly."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        measurement = FieldMeasurement(
            components=(3.0, 4.0, 0.0),
            timestamp=timestamp
        )
        
        import math
        assert math.isclose(measurement.norm, 5.0, rel_tol=1e-9)
