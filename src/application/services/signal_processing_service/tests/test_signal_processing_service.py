"""
Tests for SignalProcessingService.
Verifies processing, calibration, and automatic calibration workflow.
"""
import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel
from application.services.signal_processing_service.signal_processing_service import SignalProcessingService


class TestSignalProcessingService(unittest.TestCase):
    """Test SignalProcessingService operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = SignalProcessingService()
        self.timestamp = datetime.now()
        
        self.measurement = VoltageMeasurement(
            voltage_x_in_phase=3.0,
            voltage_x_quadrature=4.0,
            voltage_y_in_phase=5.0,
            voltage_y_quadrature=12.0,
            voltage_z_in_phase=8.0,
            voltage_z_quadrature=15.0,
            timestamp=self.timestamp
        )
        
        self.noise_offset = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=2.0,
            voltage_y_quadrature=2.0,
            voltage_z_in_phase=3.0,
            voltage_z_quadrature=3.0,
            timestamp=self.timestamp
        )
    
    def test_process_measurement_without_reference(self):
        """Test that processing without reference returns unchanged measurement."""
        result = self.service.process_measurement(self.measurement)
        self.assertEqual(result, self.measurement)
    
    def test_process_measurement_with_noise_correction(self):
        """Test processing with noise correction only."""
        self.service.calibrate_noise(self.noise_offset)
        result = self.service.process_measurement(self.measurement)
        
        # Should have noise subtracted
        self.assertAlmostEqual(result.voltage_x_in_phase, 2.0)
        self.assertAlmostEqual(result.voltage_x_quadrature, 3.0)
    
    def test_process_measurement_with_phase_correction(self):
        """Test processing with phase correction."""
        # Calibrate phase
        self.service.calibrate_phase(self.measurement)
        
        # Process measurement
        result = self.service.process_measurement(self.measurement)
        
        # Quadrature should be zero after phase correction
        self.assertAlmostEqual(result.voltage_x_quadrature, 0.0, places=10)
        self.assertAlmostEqual(result.voltage_y_quadrature, 0.0, places=10)
        self.assertAlmostEqual(result.voltage_z_quadrature, 0.0, places=10)
    
    def test_process_measurement_with_primary_correction(self):
        """Test processing with primary field correction."""
        primary_offset = VoltageMeasurement(
            voltage_x_in_phase=0.5,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=1.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=2.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        self.service.calibrate_primary(primary_offset)
        result = self.service.process_measurement(self.measurement)
        
        # Should have primary offset subtracted
        self.assertAlmostEqual(result.voltage_x_in_phase, 2.5)
        self.assertAlmostEqual(result.voltage_y_in_phase, 4.0)
        self.assertAlmostEqual(result.voltage_z_in_phase, 6.0)
    
    def test_process_measurement_with_all_corrections(self):
        """Test processing with all corrections applied in order."""
        # Setup all calibrations
        self.service.calibrate_noise(self.noise_offset)
        self.service.calibrate_phase(self.measurement)
        primary_offset = VoltageMeasurement(
            voltage_x_in_phase=0.5,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=1.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=2.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        self.service.calibrate_primary(primary_offset)
        
        # Process
        result = self.service.process_measurement(self.measurement)
        
        # Should have all corrections applied
        # Noise: (3,4) - (1,1) = (2,3)
        # Phase: align (2,3) -> (mag, 0) where mag = sqrt(2²+3²) = sqrt(13)
        # Primary: (mag, 0) - (0.5, 0) = (mag-0.5, 0)
        expected_mag = (3.0 - 1.0)**2 + (4.0 - 1.0)**2
        expected_mag = expected_mag ** 0.5
        self.assertAlmostEqual(result.voltage_x_in_phase, expected_mag - 0.5, places=5)
        self.assertAlmostEqual(result.voltage_x_quadrature, 0.0, places=10)
    
    def test_calibrate_phase_calculates_angles(self):
        """Test that calibrate_phase calculates angles correctly."""
        self.service.calibrate_phase(self.measurement)
        reference = self.service.get_reference()
        
        self.assertIsNotNone(reference)
        self.assertTrue(reference.is_phase_calibrated())
        self.assertIn('x', reference.phase_angles)
        self.assertIn('y', reference.phase_angles)
        self.assertIn('z', reference.phase_angles)
    
    def test_calibrate_with_position_and_excitation_context(self):
        """Test calibration with position and excitation context."""
        position = Position2D(x=10.0, y=20.0)
        excitation = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
        
        self.service.calibrate_noise(self.noise_offset, position, excitation)
        reference = self.service.get_reference()
        
        self.assertEqual(reference.calibration_position, position)
        self.assertEqual(reference.excitation_parameters, excitation)
    
    def test_set_and_get_reference(self):
        """Test setting and getting reference."""
        reference = VoltageMeasurementReference(
            noise_offset=self.noise_offset,
            phase_angles={'x': 0.1, 'y': 0.2, 'z': 0.3}
        )
        
        self.service.set_reference(reference)
        retrieved = self.service.get_reference()
        
        self.assertEqual(retrieved, reference)
    
    def test_reset_calibration(self):
        """Test resetting calibration."""
        self.service.calibrate_noise(self.noise_offset)
        self.assertIsNotNone(self.service.get_reference())
        
        self.service.reset_calibration()
        self.assertIsNone(self.service.get_reference())
    
    def test_perform_automatic_calibration_full_sequence(self):
        """Test automatic calibration performs all steps."""
        # Create mocks
        acquisition_port = Mock()
        excitation_port = Mock()
        motion_port = Mock()
        
        # Setup mock returns
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        phase_measurement = VoltageMeasurement(
            voltage_x_in_phase=3.0,
            voltage_x_quadrature=4.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        primary_measurement = VoltageMeasurement(
            voltage_x_in_phase=5.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        acquisition_port.acquire_sample.side_effect = [
            noise_measurement,
            phase_measurement,
            primary_measurement
        ]
        
        target_position = Position2D(x=10.0, y=20.0)
        excitation_params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        
        # Perform automatic calibration
        reference = self.service.perform_automatic_calibration(
            acquisition_port,
            excitation_port,
            motion_port,
            target_position,
            excitation_params
        )
        
        # Verify all steps were called
        motion_port.move_to.assert_called_once_with(target_position)
        self.assertEqual(excitation_port.apply_excitation.call_count, 2)  # Off, then On
        self.assertEqual(acquisition_port.acquire_sample.call_count, 3)  # Noise, Phase, Primary
        
        # Verify reference is complete
        self.assertIsNotNone(reference)
        self.assertTrue(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertTrue(reference.is_primary_calibrated())
        self.assertEqual(reference.calibration_position, target_position)
    
    def test_perform_automatic_calibration_noise_step(self):
        """Test automatic calibration noise step."""
        acquisition_port = Mock()
        excitation_port = Mock()
        
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        acquisition_port.acquire_sample.return_value = noise_measurement
        
        excitation_params = ExcitationParameters.off()
        
        # Perform only noise step (by calling calibrate_noise directly)
        self.service.calibrate_noise(noise_measurement)
        
        # Verify noise is calibrated
        reference = self.service.get_reference()
        self.assertIsNotNone(reference)
        self.assertTrue(reference.is_noise_calibrated())
        self.assertEqual(reference.noise_offset, noise_measurement)
    
    def test_perform_automatic_calibration_phase_step(self):
        """Test automatic calibration phase step."""
        # First calibrate noise
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        self.service.calibrate_noise(noise_measurement)
        
        # Then calibrate phase
        phase_measurement = VoltageMeasurement(
            voltage_x_in_phase=3.0,
            voltage_x_quadrature=4.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Process to apply noise correction first
        phase_measurement_corrected = self.service.process_measurement(phase_measurement)
        self.service.calibrate_phase(phase_measurement_corrected)
        
        # Verify phase is calibrated
        reference = self.service.get_reference()
        self.assertTrue(reference.is_phase_calibrated())
    
    def test_perform_automatic_calibration_primary_step(self):
        """Test automatic calibration primary step."""
        # Setup noise and phase first
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        self.service.calibrate_noise(noise_measurement)
        
        phase_measurement = VoltageMeasurement(
            voltage_x_in_phase=3.0,
            voltage_x_quadrature=4.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        phase_measurement_corrected = self.service.process_measurement(phase_measurement)
        self.service.calibrate_phase(phase_measurement_corrected)
        
        # Then calibrate primary
        primary_measurement = VoltageMeasurement(
            voltage_x_in_phase=5.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Process to apply noise+phase correction first
        primary_measurement_corrected = self.service.process_measurement(primary_measurement)
        self.service.calibrate_primary(primary_measurement_corrected)
        
        # Verify primary is calibrated
        reference = self.service.get_reference()
        self.assertTrue(reference.is_primary_calibrated())


if __name__ == "__main__":
    unittest.main()
