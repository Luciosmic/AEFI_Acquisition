"""
End-to-End Tests for Signal Processing API Service

Responsibility:
    Test the complete signal processing workflow using fakes and simulators.
    Validates orchestration, calibration, processing, and persistence.

Rationale:
    - Uses realistic fakes (ExcitationAwareAcquisitionPort) for deterministic testing
    - Tests complete workflows, not just unit operations
    - Validates integration between API, service, and infrastructure
    - Ensures robustness and determinism

Design:
    - Uses ExcitationAwareAcquisitionPort (simulator with excitation coupling)
    - Uses MockExcitationPort and MockMotionPort
    - Uses real repository (JsonVoltageMeasurementReferenceRepository) with temp dir
    - Tests automatic calibration sequence
    - Tests processing with calibration
    - Tests persistence operations
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
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.persistence.json_voltage_measurement_reference_repository import JsonVoltageMeasurementReferenceRepository
from application.services.signal_processing_service.signal_processing_api_service import SignalProcessingApiService
from application.services.signal_processing_service.dtos.signal_processing_request_dtos import (
    ProcessMeasurementRequest,
    CalibrateNoiseRequest,
    CalibratePhaseRequest,
    CalibratePrimaryRequest,
    ResetCalibrationRequest
)




class TestSignalProcessingApiServiceE2E(unittest.TestCase):
    """End-to-end tests for Signal Processing API Service."""
    
    def setUp(self):
        """Set up test fixtures with realistic fakes."""
        # Create temporary directory for repository
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup infrastructure fakes (sources de vérité)
        # Base acquisition port with deterministic noise (seed=42 for reproducibility)
        base_acquisition = RandomNoiseAcquisitionPort(noise_std=0.01, seed=42)
        
        # Excitation port
        self.excitation_port = MockExcitationPort()
        
        # Motion port
        self.motion_port = MockMotionPort(motion_delay_ms=10.0)
        
        # Excitation-aware acquisition port (simulator with realistic coupling)
        self.acquisition_port = ExcitationAwareAcquisitionPort(
            base_acquisition_port=base_acquisition,
            excitation_port=self.excitation_port,
            real_ratio=0.9,  # 90% real, 10% quadrature
            offset_scale=1.0
        )
        
        # Repository
        self.repository = JsonVoltageMeasurementReferenceRepository(base_config_dir=self.temp_dir)
        
        # API Service
        self.api_service = SignalProcessingApiService(
            acquisition_port=self.acquisition_port,
            excitation_port=self.excitation_port,
            motion_port=self.motion_port,
            repository=self.repository
        )
        
        self.timestamp = datetime.now()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_automatic_calibration_sequence(self):
        """Test complete automatic calibration sequence."""
        # Setup excitation parameters
        excitation_params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
        
        # Target position
        target_position = Position2D(100.0, 200.0)
        
        # Perform automatic calibration
        reference = self.api_service.perform_automatic_calibration(
            target_position=target_position,
            excitation_params=excitation_params
        )
        
        # Verify reference is complete
        self.assertIsNotNone(reference)
        self.assertTrue(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertTrue(reference.is_primary_calibrated())
        
        # Verify position and excitation are recorded
        self.assertIsNotNone(reference.calibration_position)
        self.assertEqual(reference.calibration_position.x, 100.0)
        self.assertEqual(reference.calibration_position.y, 200.0)
        self.assertIsNotNone(reference.excitation_parameters)
        self.assertEqual(reference.excitation_parameters.mode, ExcitationMode.X_DIR)
        
        # Verify motion was called once (at the beginning, then 3 acquisitions at same position)
        self.assertEqual(len(self.motion_port.move_history), 1)  # Single move at start
        self.assertEqual(self.motion_port.move_history[0].x, 100.0)
        self.assertEqual(self.motion_port.move_history[0].y, 200.0)
    
    def test_manual_calibration_workflow(self):
        """Test manual calibration workflow step by step."""
        # Step 1: Calibrate noise (excitation off)
        request = CalibrateNoiseRequest(
            reference_measurement=None,
            position=Position2D(50.0, 50.0),
            excitation=None  # Will default to off
        )
        self.api_service.calibrate_noise(request)
        
        # Verify noise is calibrated
        reference = self.api_service.get_current_reference()
        self.assertIsNotNone(reference)
        self.assertTrue(reference.is_noise_calibrated())
        self.assertFalse(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # Step 2: Calibrate phase (excitation on)
        excitation = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(excitation)
        
        request = CalibratePhaseRequest(
            reference_measurement=None,
            position=Position2D(50.0, 50.0),
            excitation=excitation
        )
        self.api_service.calibrate_phase(request)
        
        # Verify phase is calibrated
        reference = self.api_service.get_current_reference()
        self.assertTrue(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # Step 3: Calibrate primary (excitation still on)
        request = CalibratePrimaryRequest(
            reference_measurement=None,
            position=Position2D(50.0, 50.0),
            excitation=excitation
        )
        self.api_service.calibrate_primary(request)
        
        # Verify all are calibrated
        reference = self.api_service.get_current_reference()
        self.assertTrue(reference.is_noise_calibrated())
        self.assertTrue(reference.is_phase_calibrated())
        self.assertTrue(reference.is_primary_calibrated())
    
    def test_calibration_with_provided_measurement(self):
        """Test calibration using provided measurements (no orchestration)."""
        # Create a measurement manually
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=0.1,
            voltage_x_quadrature=0.05,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # Calibrate noise with provided measurement
        request = CalibrateNoiseRequest(reference_measurement=noise_measurement)
        self.api_service.calibrate_noise(request)
        
        # Verify
        reference = self.api_service.get_current_reference()
        self.assertTrue(reference.is_noise_calibrated())
        self.assertEqual(reference.noise_offset.voltage_x_in_phase, 0.1)
        
        # Motion should not have been called
        self.assertEqual(len(self.motion_port.move_history), 0)
    
    def test_processing_with_calibration(self):
        """Test processing measurements with calibration applied."""
        # Setup calibration
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=0.5,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        request = CalibrateNoiseRequest(reference_measurement=noise_measurement)
        self.api_service.calibrate_noise(request)
        
        # Process a measurement
        raw_measurement = VoltageMeasurement(
            voltage_x_in_phase=2.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        request = ProcessMeasurementRequest(measurement=raw_measurement)
        response = self.api_service.process_measurement(request)
        processed = response.processed_measurement
        
        # Verify noise correction applied
        self.assertAlmostEqual(processed.voltage_x_in_phase, 1.0, places=5)
        self.assertAlmostEqual(processed.voltage_x_quadrature, 0.5, places=5)
    
    def test_persistence_save_and_load(self):
        """Test saving and loading calibration reference."""
        # Setup calibration
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=0.1,
            voltage_x_quadrature=0.05,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        request = CalibrateNoiseRequest(reference_measurement=noise_measurement)
        self.api_service.calibrate_noise(request)
        
        # Save reference
        name = self.api_service.save_reference(name="test_calibration")
        self.assertEqual(name, "test_calibration")
        
        # Reset calibration
        request = ResetCalibrationRequest()
        self.api_service.reset_calibration(request)
        reference = self.api_service.get_current_reference()
        # After reset, reference should be empty (not calibrated)
        self.assertIsNotNone(reference)
        self.assertFalse(reference.is_noise_calibrated())
        self.assertFalse(reference.is_phase_calibrated())
        self.assertFalse(reference.is_primary_calibrated())
        
        # Load reference
        loaded = self.api_service.load_reference("test_calibration")
        self.assertIsNotNone(loaded)
        self.assertTrue(loaded.is_noise_calibrated())
        self.assertEqual(loaded.noise_offset.voltage_x_in_phase, 0.1)
        
        # Verify current reference is set
        current = self.api_service.get_current_reference()
        self.assertIsNotNone(current)
        self.assertEqual(current.noise_offset.voltage_x_in_phase, 0.1)
    
    def test_persistence_list_and_delete(self):
        """Test listing and deleting saved references."""
        # Create and save multiple references
        for i in range(3):
            noise_measurement = VoltageMeasurement(
                voltage_x_in_phase=float(i),
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=self.timestamp
            )
            request = CalibrateNoiseRequest(reference_measurement=noise_measurement)
            self.api_service.calibrate_noise(request)
            self.api_service.save_reference(name=f"calibration_{i}")
        
        # List all references
        all_names = self.api_service.list_saved_references()
        self.assertEqual(len(all_names), 3)
        self.assertIn("calibration_0", all_names)
        self.assertIn("calibration_1", all_names)
        self.assertIn("calibration_2", all_names)
        
        # Delete one
        deleted = self.api_service.delete_reference("calibration_1")
        self.assertTrue(deleted)
        
        # Verify it's gone
        all_names = self.api_service.list_saved_references()
        self.assertEqual(len(all_names), 2)
        self.assertNotIn("calibration_1", all_names)
        
        # Try to load deleted reference
        loaded = self.api_service.load_reference("calibration_1")
        self.assertIsNone(loaded)
    
    def test_calibration_status(self):
        """Test getting calibration status."""
        # Initially no calibration
        status = self.api_service.get_calibration_status()
        self.assertFalse(status["calibrated"])
        self.assertFalse(status["noise_calibrated"])
        self.assertFalse(status["phase_calibrated"])
        self.assertFalse(status["primary_calibrated"])
        
        # Calibrate noise
        noise_measurement = VoltageMeasurement(
            voltage_x_in_phase=0.1,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        request = CalibrateNoiseRequest(reference_measurement=noise_measurement)
        self.api_service.calibrate_noise(request)
        
        # Check status
        status = self.api_service.get_calibration_status()
        self.assertTrue(status["calibrated"])
        self.assertTrue(status["noise_calibrated"])
        self.assertFalse(status["phase_calibrated"])
        self.assertFalse(status["primary_calibrated"])
    
    def test_full_workflow_with_excitation_coupling(self):
        """Test complete workflow with excitation-aware acquisition simulator."""
        # This test validates that the excitation coupling in ExcitationAwareAcquisitionPort
        # works correctly with the calibration workflow
        
        # Set excitation to X_DIR
        excitation = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(excitation)
        
        # Acquire a sample (will have X_DIR offset applied by simulator)
        raw_sample = self.acquisition_port.acquire_sample()
        
        # Verify sample has offset (from ExcitationAwareAcquisitionPort)
        # The simulator applies offset based on excitation mode
        self.assertNotEqual(raw_sample.voltage_x_in_phase, 0.0)
        
        # Calibrate noise with this sample
        request = CalibrateNoiseRequest(reference_measurement=raw_sample)
        self.api_service.calibrate_noise(request)
        
        # Process the same sample (should subtract noise)
        request = ProcessMeasurementRequest(measurement=raw_sample)
        response = self.api_service.process_measurement(request)
        processed = response.processed_measurement
        
        # After noise correction, the offset should be removed
        # (within noise tolerance)
        self.assertAlmostEqual(processed.voltage_x_in_phase, 0.0, delta=0.02)


if __name__ == "__main__":
    unittest.main()
