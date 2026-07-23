"""
Tests for ElectricFieldScanPointAcquired event
"""

from uuid import uuid4
from datetime import datetime
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired


class TestElectricFieldScanPointAcquired:
    """Tests for ElectricFieldScanPointAcquired event."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        scan_id = uuid4()
        position = Position2D(x=1.0, y=2.0)
        field_measurement = FieldMeasurement(
            components=(1.5, 2.5, 3.5),
            timestamp=datetime.now(),
            uncertainty_estimate=0.1,
            std_dev_components=(0.05, 0.05, 0.05)
        )
        
        event = ElectricFieldScanPointAcquired(
            scan_id=scan_id,
            point_index=5,
            position=position,
            field_measurement=field_measurement
        )
        
        assert event.scan_id == scan_id
        assert event.point_index == 5
        assert event.position == position
        assert event.field_measurement == field_measurement
    
    def test_event_is_frozen(self):
        """Test that event is immutable."""
        scan_id = uuid4()
        position = Position2D(x=1.0, y=2.0)
        field_measurement = FieldMeasurement(
            components=(1.0, 2.0, 3.0),
            timestamp=datetime.now()
        )
        
        event = ElectricFieldScanPointAcquired(
            scan_id=scan_id,
            point_index=0,
            position=position,
            field_measurement=field_measurement
        )
        
        try:
            event.point_index = 10
            assert False, "Event should be frozen"
        except Exception:
            pass  # Expected
    
    def test_event_with_mono_axial_measurement(self):
        """Test event with mono-axial field measurement."""
        field_measurement = FieldMeasurement(
            components=(5.0,),
            timestamp=datetime.now(),
            std_dev_components=(0.1,)
        )
        
        event = ElectricFieldScanPointAcquired(
            scan_id=uuid4(),
            point_index=0,
            position=Position2D(x=0.0, y=0.0),
            field_measurement=field_measurement
        )
        
        assert len(event.field_measurement.components) == 1
        assert event.field_measurement.std_dev_components == (0.1,)
    
    def test_event_with_tri_axial_measurement(self):
        """Test event with tri-axial field measurement."""
        field_measurement = FieldMeasurement(
            components=(1.0, 2.0, 3.0),
            timestamp=datetime.now(),
            std_dev_components=(0.1, 0.2, 0.3)
        )
        
        event = ElectricFieldScanPointAcquired(
            scan_id=uuid4(),
            point_index=0,
            position=Position2D(x=1.0, y=2.0),
            field_measurement=field_measurement
        )
        
        assert len(event.field_measurement.components) == 3
        assert event.field_measurement.std_dev_components == (0.1, 0.2, 0.3)
