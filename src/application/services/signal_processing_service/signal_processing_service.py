"""
Application: Signal Processing Service (Use Case)

Responsibility:
    Orchestrate signal processing corrections (Noise, Phase, Primary).
    Manages calibration reference and applies corrections to measurements.

Rationale:
    - Application layer orchestrates domain logic
    - Encapsulates calibration state
    - Provides automatic calibration workflow
    - Used internally by SignalProcessingApiService

Design:
    - Use case implementation (not a public interface)
    - Uses domain services for pure logic
    - Coordinates with ports for hardware operations
"""
from typing import Optional
import time
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.services.signal_calibration_service import SignalCalibrationService
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from application.services.motion_control_service.i_motion_port import IMotionPort


class SignalProcessingService:
    """
    Application service for signal processing operations.
    
    Orchestrates corrections and manages calibration reference.
    """
    
    def __init__(self):
        """Initialize signal processing service."""
        self._reference: Optional[VoltageMeasurementReference] = None
        self._calibration_service = SignalCalibrationService()
    
    def process_measurement(self, measurement: VoltageMeasurement) -> VoltageMeasurement:
        """
        Apply signal processing corrections to a measurement.
        
        Applies corrections in order: Noise → Phase → Primary
        (if calibration reference is set).
        
        Args:
            measurement: Raw voltage measurement to process
        
        Returns:
            Processed voltage measurement with corrections applied
        """
        if self._reference is None:
            return measurement
        
        result = measurement
        
        # 1. Noise correction
        if self._reference.is_noise_calibrated():
            result = result.apply_noise_correction(self._reference.noise_offset)
        
        # 2. Phase correction
        if self._reference.is_phase_calibrated():
            result = result.apply_phase_correction(self._reference.phase_angles)
        
        # 3. Primary field correction
        if self._reference.is_primary_calibrated():
            result = result.apply_primary_field_correction(self._reference.primary_offset)
        
        return result
    
    def calibrate_noise(
        self,
        reference_measurement: VoltageMeasurement,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None
    ) -> None:
        """
        Calibrate noise offset using a reference measurement.
        
        Args:
            reference_measurement: Measurement to use as noise offset
            position: Optional position where calibration was performed
            excitation: Optional excitation parameters during calibration
        """
        if self._reference is None:
            # Create new reference
            self._reference = VoltageMeasurementReference(
                noise_offset=reference_measurement,
                calibration_position=position,
                excitation_parameters=excitation
            )
        else:
            # Update existing reference
            self._reference = self._reference.with_noise_offset(reference_measurement)
            if position is not None or excitation is not None:
                self._reference = self._reference.with_calibration_context(position, excitation)
    
    def calibrate_phase(
        self,
        reference_measurement: VoltageMeasurement,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None
    ) -> None:
        """
        Calibrate phase angles using a reference measurement.
        
        Args:
            reference_measurement: Measurement to use for phase calculation
            position: Optional position where calibration was performed
            excitation: Optional excitation parameters during calibration
        """
        # Calculate phase angles using domain service
        phase_angles = self._calibration_service.calculate_phase_angles(reference_measurement)
        
        if self._reference is None:
            # Create new reference
            self._reference = VoltageMeasurementReference(
                phase_angles=phase_angles,
                calibration_position=position,
                excitation_parameters=excitation
            )
        else:
            # Update existing reference
            self._reference = self._reference.with_phase_angles(phase_angles)
            if position is not None or excitation is not None:
                self._reference = self._reference.with_calibration_context(position, excitation)
    
    def calibrate_primary(
        self,
        reference_measurement: VoltageMeasurement,
        position: Optional[Position2D] = None,
        excitation: Optional[ExcitationParameters] = None
    ) -> None:
        """
        Calibrate primary field offset using a reference measurement.
        
        Args:
            reference_measurement: Measurement to use as primary offset
            position: Optional position where calibration was performed
            excitation: Optional excitation parameters during calibration
        """
        if self._reference is None:
            # Create new reference
            self._reference = VoltageMeasurementReference(
                primary_offset=reference_measurement,
                calibration_position=position,
                excitation_parameters=excitation
            )
        else:
            # Update existing reference
            self._reference = self._reference.with_primary_offset(reference_measurement)
            if position is not None or excitation is not None:
                self._reference = self._reference.with_calibration_context(position, excitation)
    
    def perform_automatic_calibration(
        self,
        acquisition_port: IAcquisitionPort,
        excitation_port: IExcitationPort,
        motion_port: Optional[IMotionPort],
        target_position: Optional[Position2D],
        excitation_params: ExcitationParameters
    ) -> VoltageMeasurementReference:
        """
        Perform complete automatic calibration sequence.
        
        Steps:
        1. Noise calibration: Move to position, turn off excitation, acquire reference
        2. Phase calibration: Turn on excitation, acquire reference (after noise correction)
        3. Primary calibration: Maintain excitation, acquire reference (after noise+phase correction)
        
        Args:
            acquisition_port: Port for acquiring measurements
            excitation_port: Port for controlling excitation
            motion_port: Optional port for motion control
            target_position: Optional target position for calibration
            excitation_params: Excitation parameters for phase and primary calibration
        
        Returns:
            Complete VoltageMeasurementReference with all calibration parameters
        """
        # Step 1: Noise calibration
        # Move to target position if motion port and position provided
        if motion_port is not None and target_position is not None:
            motion_port.move_to(target_position)
            # Wait for motion to complete (simple wait, could be improved with events)
            time.sleep(0.5)
        
        # Turn off excitation
        excitation_off = ExcitationParameters.off()
        excitation_port.apply_excitation(excitation_off)
        time.sleep(0.1)  # Wait for stabilization
        
        # Acquire noise reference
        noise_measurement = acquisition_port.acquire_sample()
        self.calibrate_noise(noise_measurement, target_position, excitation_off)
        
        # Step 2: Phase calibration
        # Turn on excitation
        excitation_port.apply_excitation(excitation_params)
        time.sleep(0.1)  # Wait for stabilization
        
        # Acquire phase reference (after noise correction)
        phase_measurement_raw = acquisition_port.acquire_sample()
        phase_measurement = self.process_measurement(phase_measurement_raw)  # Apply noise correction
        self.calibrate_phase(phase_measurement, target_position, excitation_params)
        
        # Step 3: Primary field calibration
        # Maintain excitation
        # Acquire primary reference (after noise+phase correction)
        primary_measurement_raw = acquisition_port.acquire_sample()
        primary_measurement = self.process_measurement(primary_measurement_raw)  # Apply noise+phase correction
        self.calibrate_primary(primary_measurement, target_position, excitation_params)
        
        # Return complete reference
        return self._reference
    
    def set_reference(self, reference: VoltageMeasurementReference) -> None:
        """
        Set the calibration reference to use for processing.
        
        Args:
            reference: VoltageMeasurementReference to use
        """
        self._reference = reference
    
    def get_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Get the current calibration reference.
        
        Returns:
            Current VoltageMeasurementReference, or None if not set
        """
        return self._reference
    
    def reset_calibration(self) -> None:
        """
        Reset all calibration parameters.
        """
        self._reference = None
