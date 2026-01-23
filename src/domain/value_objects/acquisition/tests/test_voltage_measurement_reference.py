"""
Tests for VoltageMeasurementReference.
Verifies immutability, builder pattern, and calibration flags.
"""
import unittest
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel


class TestVoltageMeasurementReference(unittest.TestCase):
    """Test VoltageMeasurementReference immutability and methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=2.0,
            voltage_y_in_phase=3.0,
            voltage_y_quadrature=4.0,
            voltage_z_in_phase=5.0,
            voltage_z_quadrature=6.0,
            timestamp=self.timestamp
        )
        self.position = Position2D(x=10.0, y=20.0)
        self.excitation = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
    
    def test_voltage_measurement_reference_creation(self):
        """Test creating a reference with all parameters."""
        reference = VoltageMeasurementReference(
            noise_offset=self.measurement,
            phase_angles={'x': 0.1, 'y': 0.2, 'z': 0.3},
            primary_offset=self.measurement,
            calibration_timestamp=self.timestamp,
            calibration_author="test_user",
            calibration_position=self.position,
            excitation_parameters=self.excitation
        )
        
        self.assertEqual(reference.noise_offset, self.measurement)
        self.assertEqual(reference.phase_angles['x'], 0.1)
        self.assertEqual(reference.primary_offset, self.measurement)
        self.assertEqual(reference.calibration_author, "test_user")
        self.assertEqual(reference.calibration_position, self.position)
        self.assertEqual(reference.excitation_parameters, self.excitation)
    
    def test_with_noise_offset_creates_new_reference(self):
        """Test that with_noise_offset creates a new reference (immutability)."""
        reference1 = VoltageMeasurementReference()
        reference2 = reference1.with_noise_offset(self.measurement)
        
        # Original should be unchanged
        self.assertIsNone(reference1.noise_offset)
        
        # New reference should have the offset
        self.assertEqual(reference2.noise_offset, self.measurement)
        
        # Should be different objects
        self.assertIsNot(reference1, reference2)
    
    def test_with_phase_angles_creates_new_reference(self):
        """Test that with_phase_angles creates a new reference."""
        reference1 = VoltageMeasurementReference()
        angles = {'x': 0.1, 'y': 0.2, 'z': 0.3}
        reference2 = reference1.with_phase_angles(angles)
        
        # Original should be unchanged
        self.assertEqual(len(reference1.phase_angles), 0)
        
        # New reference should have the angles
        self.assertEqual(reference2.phase_angles, angles)
        
        # Should be different objects
        self.assertIsNot(reference1, reference2)
    
    def test_with_phase_angles_updates_existing(self):
        """Test that with_phase_angles updates existing angles."""
        reference1 = VoltageMeasurementReference(phase_angles={'x': 0.1})
        reference2 = reference1.with_phase_angles({'y': 0.2, 'z': 0.3})
        
        # Should have all angles
        self.assertEqual(reference2.phase_angles['x'], 0.1)
        self.assertEqual(reference2.phase_angles['y'], 0.2)
        self.assertEqual(reference2.phase_angles['z'], 0.3)
    
    def test_with_primary_offset_creates_new_reference(self):
        """Test that with_primary_offset creates a new reference."""
        reference1 = VoltageMeasurementReference()
        reference2 = reference1.with_primary_offset(self.measurement)
        
        # Original should be unchanged
        self.assertIsNone(reference1.primary_offset)
        
        # New reference should have the offset
        self.assertEqual(reference2.primary_offset, self.measurement)
        
        # Should be different objects
        self.assertIsNot(reference1, reference2)
    
    def test_with_calibration_context_creates_new_reference(self):
        """Test that with_calibration_context creates a new reference."""
        reference1 = VoltageMeasurementReference()
        reference2 = reference1.with_calibration_context(self.position, self.excitation)
        
        # Original should be unchanged
        self.assertIsNone(reference1.calibration_position)
        
        # New reference should have the context
        self.assertEqual(reference2.calibration_position, self.position)
        self.assertEqual(reference2.excitation_parameters, self.excitation)
        
        # Should be different objects
        self.assertIsNot(reference1, reference2)
    
    def test_is_calibrated_flags(self):
        """Test calibration status flags."""
        # Empty reference
        reference = VoltageMeasurementReference()
        self.assertFalse(reference.is_noise_calibrated())
        self.assertFalse(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # With noise only
        reference = reference.with_noise_offset(self.measurement)
        self.assertTrue(reference.is_noise_calibrated())
        self.assertFalse(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # With phase only
        reference = VoltageMeasurementReference().with_phase_angles({'x': 0.1, 'y': 0.2, 'z': 0.3})
        self.assertFalse(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # With primary only
        reference = VoltageMeasurementReference().with_primary_offset(self.measurement)
        self.assertFalse(reference.is_noise_calibrated())
        self.assertFalse(reference.is_phase_calibrated())
        self.assertTrue(reference.is_primary_calibrated())
        
        # With all
        reference = VoltageMeasurementReference(
            noise_offset=self.measurement,
            phase_angles={'x': 0.1, 'y': 0.2, 'z': 0.3},
            primary_offset=self.measurement
        )
        self.assertTrue(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertTrue(reference.is_primary_calibrated())
    
    def test_is_phase_calibrated_requires_all_axes(self):
        """Test that is_phase_calibrated requires all 3 axes."""
        # Partial phase angles
        reference = VoltageMeasurementReference(phase_angles={'x': 0.1, 'y': 0.2})
        self.assertFalse(reference.is_phase_calibrated())
        
        # All axes
        reference = reference.with_phase_angles({'z': 0.3})
        self.assertTrue(reference.is_phase_calibrated())
    
    def test_reference_immutability(self):
        """Test that reference is immutable (frozen dataclass)."""
        reference = VoltageMeasurementReference()
        
        # Should raise AttributeError when trying to modify attributes
        with self.assertRaises(AttributeError):
            reference.noise_offset = self.measurement
        
        # Note: phase_angles is a dict, which is mutable, but the reference itself
        # cannot be reassigned. The dict contents can be modified, but this is
        # expected behavior for frozen dataclasses with mutable fields.
        # The immutability is enforced at the reference level, not the dict level.


if __name__ == "__main__":
    unittest.main()
