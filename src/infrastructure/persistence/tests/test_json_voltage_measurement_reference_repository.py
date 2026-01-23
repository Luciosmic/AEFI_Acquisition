"""
Tests for JsonVoltageMeasurementReferenceRepository.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel
from infrastructure.persistence.json_voltage_measurement_reference_repository import JsonVoltageMeasurementReferenceRepository


class TestJsonVoltageMeasurementReferenceRepository(unittest.TestCase):
    """Test JSON repository for VoltageMeasurementReference."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = JsonVoltageMeasurementReferenceRepository(base_config_dir=self.temp_dir)
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
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load(self):
        """Test saving and loading a reference."""
        reference = VoltageMeasurementReference(
            noise_offset=self.measurement,
            phase_angles={'x': 0.1, 'y': 0.2, 'z': 0.3},
            primary_offset=self.measurement,
            calibration_timestamp=self.timestamp,
            calibration_author="test_user",
            calibration_position=self.position,
            excitation_parameters=self.excitation
        )
        
        # Save
        name = self.repo.save(reference, "test_reference")
        self.assertEqual(name, "test_reference")
        
        # Load
        loaded = self.repo.load("test_reference")
        self.assertIsNotNone(loaded)
        
        # Verify all fields
        self.assertIsNotNone(loaded.noise_offset)
        self.assertEqual(loaded.noise_offset.voltage_x_in_phase, 1.0)
        self.assertEqual(loaded.phase_angles['x'], 0.1)
        self.assertEqual(loaded.phase_angles['y'], 0.2)
        self.assertEqual(loaded.phase_angles['z'], 0.3)
        self.assertIsNotNone(loaded.primary_offset)
        self.assertEqual(loaded.calibration_author, "test_user")
        self.assertIsNotNone(loaded.calibration_position)
        self.assertEqual(loaded.calibration_position.x, 10.0)
        self.assertIsNotNone(loaded.excitation_parameters)
        self.assertEqual(loaded.excitation_parameters.mode, ExcitationMode.X_DIR)
        self.assertEqual(loaded.excitation_parameters.level.value, 50.0)
    
    def test_save_without_name_generates_from_timestamp(self):
        """Test that saving without name generates name from timestamp."""
        reference = VoltageMeasurementReference(
            calibration_timestamp=self.timestamp
        )
        
        name = self.repo.save(reference)
        expected_name = self.timestamp.strftime("%Y-%m-%d_%H%M%S")
        self.assertEqual(name, expected_name)
    
    def test_load_nonexistent_returns_none(self):
        """Test that loading nonexistent reference returns None."""
        loaded = self.repo.load("nonexistent")
        self.assertIsNone(loaded)
    
    def test_load_latest(self):
        """Test loading the latest reference."""
        # Save multiple references with different timestamps
        ref1 = VoltageMeasurementReference(
            calibration_timestamp=datetime(2024, 1, 1, 10, 0, 0),
            calibration_author="user1"
        )
        ref2 = VoltageMeasurementReference(
            calibration_timestamp=datetime(2024, 1, 1, 11, 0, 0),
            calibration_author="user2"
        )
        
        self.repo.save(ref1, "ref1")
        self.repo.save(ref2, "ref2")
        
        latest = self.repo.load_latest()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.calibration_author, "user2")
    
    def test_list_all(self):
        """Test listing all references."""
        ref1 = VoltageMeasurementReference(calibration_timestamp=self.timestamp)
        ref2 = VoltageMeasurementReference(calibration_timestamp=self.timestamp)
        
        self.repo.save(ref1, "ref1")
        self.repo.save(ref2, "ref2")
        
        all_names = self.repo.list_all()
        self.assertEqual(len(all_names), 2)
        self.assertIn("ref1", all_names)
        self.assertIn("ref2", all_names)
    
    def test_delete(self):
        """Test deleting a reference."""
        reference = VoltageMeasurementReference(calibration_timestamp=self.timestamp)
        name = self.repo.save(reference, "to_delete")
        
        # Verify it exists
        self.assertIsNotNone(self.repo.load("to_delete"))
        
        # Delete
        result = self.repo.delete("to_delete")
        self.assertTrue(result)
        
        # Verify it's gone
        self.assertIsNone(self.repo.load("to_delete"))
    
    def test_delete_nonexistent_returns_false(self):
        """Test that deleting nonexistent reference returns False."""
        result = self.repo.delete("nonexistent")
        self.assertFalse(result)
    
    def test_serialization_preserves_all_fields(self):
        """Test that serialization preserves all fields including optional ones."""
        # Reference with all fields
        reference_full = VoltageMeasurementReference(
            noise_offset=self.measurement,
            phase_angles={'x': 0.1, 'y': 0.2, 'z': 0.3},
            primary_offset=self.measurement,
            calibration_timestamp=self.timestamp,
            calibration_author="test_user",
            calibration_position=self.position,
            excitation_parameters=self.excitation
        )
        
        name = self.repo.save(reference_full, "full_reference")
        loaded = self.repo.load(name)
        
        # Verify all fields preserved
        self.assertIsNotNone(loaded.noise_offset)
        self.assertEqual(len(loaded.phase_angles), 3)
        self.assertIsNotNone(loaded.primary_offset)
        self.assertEqual(loaded.calibration_author, "test_user")
        self.assertIsNotNone(loaded.calibration_position)
        self.assertIsNotNone(loaded.excitation_parameters)
        
        # Reference with minimal fields
        reference_minimal = VoltageMeasurementReference(
            calibration_timestamp=self.timestamp
        )
        
        name_min = self.repo.save(reference_minimal, "minimal_reference")
        loaded_min = self.repo.load(name_min)
        
        # Verify None fields are preserved
        self.assertIsNone(loaded_min.noise_offset)
        self.assertEqual(len(loaded_min.phase_angles), 0)
        self.assertIsNone(loaded_min.primary_offset)
        self.assertIsNone(loaded_min.calibration_author)
        self.assertIsNone(loaded_min.calibration_position)
        self.assertIsNone(loaded_min.excitation_parameters)


if __name__ == "__main__":
    unittest.main()
