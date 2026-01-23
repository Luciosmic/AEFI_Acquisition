"""
Application: Signal Processing API Service (Implémentation)

Responsibility:
    Implémentation concrète de l'API Signal Processing.
    Orchestre SignalProcessingService avec les ports infrastructure.

Rationale:
    - Implémente IApiSignalProcessingService (contrat API)
    - Utilise SignalProcessingService (service application/use case) en interne
    - Orchestre les ports infrastructure (IAcquisitionPort, IExcitationPort, etc.)
    - Expose une API simple et cohérente pour les opérations de signal processing

Design:
    - Implémentation de IApiSignalProcessingService
    - Utilise SignalProcessingService (service application) en interne
    - Orchestre les ports infrastructure (injectés via constructeur)
    - Script exécutable (if __name__ == "__main__") pour démonstration
"""
from typing import Optional
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.repositories.i_voltage_measurement_reference_repository import IVoltageMeasurementReferenceRepository
from .signal_processing_service import SignalProcessingService
from .i_api_signal_processing_service import IApiSignalProcessingService
from .dtos.signal_processing_request_dtos import (
    ProcessMeasurementRequest,
    CalibrateNoiseRequest,
    CalibratePhaseRequest,
    CalibratePrimaryRequest,
    ResetCalibrationRequest
)
from .dtos.signal_processing_response_dtos import (
    ProcessMeasurementResponse,
    CalibrateNoiseResponse,
    CalibratePhaseResponse,
    CalibratePrimaryResponse,
    ResetCalibrationResponse
)


class SignalProcessingApiService(IApiSignalProcessingService):
    """
    Implémentation de l'API Signal Processing.
    
    Cette classe implémente IApiSignalProcessingService et orchestre
    SignalProcessingService avec les ports infrastructure.
    
    Architecture:
    - Implémente IApiSignalProcessingService (contrat API)
    - Utilise SignalProcessingService (service application/use case) en interne
    - Orchestre les ports infrastructure (IAcquisitionPort, IExcitationPort, IMotionPort, IVoltageMeasurementReferenceRepository)
    - Les ports infrastructure sont injectés via le constructeur
    
    Utilisée par:
    - La couche interface (view_model) pour exposer les fonctionnalités à l'UI
    - Les tests d'intégration pour valider l'orchestration complète
    """
    
    def __init__(
        self,
        acquisition_port: IAcquisitionPort,
        excitation_port: IExcitationPort,
        motion_port: Optional[IMotionPort] = None,
        repository: Optional[IVoltageMeasurementReferenceRepository] = None
    ):
        """
        Initialize API service.
        
        Args:
            acquisition_port: Port for acquiring measurements
            excitation_port: Port for controlling excitation
            motion_port: Optional port for motion control
            repository: Optional repository for persistence
        """
        self._service = SignalProcessingService()
        self._acquisition_port = acquisition_port
        self._excitation_port = excitation_port
        self._motion_port = motion_port
        self._repository = repository
    
    # ========================================================================
    # API Methods - Processing
    # ========================================================================
    
    def process_measurement(
        self,
        request: ProcessMeasurementRequest
    ) -> ProcessMeasurementResponse:
        """
        Process a measurement with current calibration.
        
        Args:
            request: ProcessMeasurementRequest containing measurement to process
        
        Returns:
            ProcessMeasurementResponse with processed measurement and applied reference
        """
        return self._service.process_measurement(request)
    
    # ========================================================================
    # API Methods - Calibration
    # ========================================================================
    
    def calibrate_noise(
        self,
        request: CalibrateNoiseRequest
    ) -> CalibrateNoiseResponse:
        """
        Calibrate noise offset.
        
        If request.reference_measurement is provided, uses it directly.
        Otherwise, orchestrates acquisition.
        
        Args:
            request: CalibrateNoiseRequest with reference measurement and optional context
        
        Returns:
            CalibrateNoiseResponse with new reference
        """
        # If reference_measurement not provided, orchestrate acquisition
        if request.reference_measurement is None:
            # Move to position if needed
            if self._motion_port is not None and request.position is not None:
                self._motion_port.move_to(request.position)
                self._motion_port.wait_until_stopped()
            
            # Set excitation (off by default for noise calibration)
            excitation = request.excitation
            if excitation is None:
                excitation = ExcitationParameters.off()
            self._excitation_port.apply_excitation(excitation)
            
            # Wait for stabilization
            import time
            time.sleep(0.1)
            
            # Acquire reference
            reference_measurement = self._acquisition_port.acquire_sample()
            
            # Update request with acquired measurement
            request = CalibrateNoiseRequest(
                reference_measurement=reference_measurement,
                position=request.position,
                excitation=excitation
            )
        
        # Delegate to service (which uses DTOs)
        return self._service.calibrate_noise(request)
    
    def calibrate_phase(
        self,
        request: CalibratePhaseRequest
    ) -> CalibratePhaseResponse:
        """
        Calibrate phase angles.
        
        If request.reference_measurement is provided, uses it directly (should be noise-corrected).
        Otherwise, orchestrates acquisition.
        
        Args:
            request: CalibratePhaseRequest with reference measurement and optional context
        
        Returns:
            CalibratePhaseResponse with new reference
        """
        # If reference_measurement not provided, orchestrate acquisition
        if request.reference_measurement is None:
            if request.excitation is None:
                raise ValueError("Excitation parameters required for phase calibration")
            
            # Move to position if needed
            if self._motion_port is not None and request.position is not None:
                self._motion_port.move_to(request.position)
                self._motion_port.wait_until_stopped()
            
            # Set excitation
            self._excitation_port.apply_excitation(request.excitation)
            
            # Wait for stabilization
            import time
            time.sleep(0.1)
            
            # Acquire reference (after noise correction)
            reference_measurement_raw = self._acquisition_port.acquire_sample()
            process_request = ProcessMeasurementRequest(measurement=reference_measurement_raw)
            process_response = self._service.process_measurement(process_request)
            reference_measurement = process_response.processed_measurement
            
            # Update request with acquired measurement
            request = CalibratePhaseRequest(
                reference_measurement=reference_measurement,
                position=request.position,
                excitation=request.excitation
            )
        
        # Delegate to service (which uses DTOs)
        return self._service.calibrate_phase(request)
    
    def calibrate_primary(
        self,
        request: CalibratePrimaryRequest
    ) -> CalibratePrimaryResponse:
        """
        Calibrate primary field offset.
        
        If request.reference_measurement is provided, uses it directly (should be noise+phase-corrected).
        Otherwise, orchestrates acquisition.
        
        Args:
            request: CalibratePrimaryRequest with reference measurement and optional context
        
        Returns:
            CalibratePrimaryResponse with new reference
        """
        # If reference_measurement not provided, orchestrate acquisition
        if request.reference_measurement is None:
            if request.excitation is None:
                raise ValueError("Excitation parameters required for primary calibration")
            
            # Move to position if needed
            if self._motion_port is not None and request.position is not None:
                self._motion_port.move_to(request.position)
                self._motion_port.wait_until_stopped()
            
            # Maintain excitation
            self._excitation_port.apply_excitation(request.excitation)
            
            # Wait for stabilization
            import time
            time.sleep(0.1)
            
            # Acquire reference (after noise+phase correction)
            reference_measurement_raw = self._acquisition_port.acquire_sample()
            process_request = ProcessMeasurementRequest(measurement=reference_measurement_raw)
            process_response = self._service.process_measurement(process_request)
            reference_measurement = process_response.processed_measurement
            
            # Update request with acquired measurement
            request = CalibratePrimaryRequest(
                reference_measurement=reference_measurement,
                position=request.position,
                excitation=request.excitation
            )
        
        # Delegate to service (which uses DTOs)
        return self._service.calibrate_primary(request)
    
    def perform_automatic_calibration(
        self,
        target_position: Optional[Position2D],
        excitation_params: ExcitationParameters
    ) -> VoltageMeasurementReference:
        """
        Perform complete automatic calibration sequence.
        
        Orchestrates: noise (excitation off) -> phase (excitation on) -> primary (excitation on).
        
        Args:
            target_position: Optional target position for calibration
            excitation_params: Excitation parameters for phase and primary calibration
        
        Returns:
            Complete VoltageMeasurementReference
        """
        import time
        
        # Step 1: Move to position if needed
        if self._motion_port is not None and target_position is not None:
            self._motion_port.move_to(target_position)
            self._motion_port.wait_until_stopped()
        
        # Step 2: Calibrate noise (excitation off)
        excitation_off = ExcitationParameters.off()
        self._excitation_port.apply_excitation(excitation_off)
        time.sleep(0.1)
        noise_measurement = self._acquisition_port.acquire_sample()
        noise_request = CalibrateNoiseRequest(
            reference_measurement=noise_measurement,
            position=target_position,
            excitation=excitation_off
        )
        self._service.calibrate_noise(noise_request)
        
        # Step 3: Calibrate phase (excitation on)
        self._excitation_port.apply_excitation(excitation_params)
        time.sleep(0.1)
        phase_measurement_raw = self._acquisition_port.acquire_sample()
        # Apply noise correction before phase calibration
        process_request = ProcessMeasurementRequest(measurement=phase_measurement_raw)
        process_response = self._service.process_measurement(process_request)
        phase_measurement = process_response.processed_measurement
        phase_request = CalibratePhaseRequest(
            reference_measurement=phase_measurement,
            position=target_position,
            excitation=excitation_params
        )
        self._service.calibrate_phase(phase_request)
        
        # Step 4: Calibrate primary (excitation still on)
        primary_measurement_raw = self._acquisition_port.acquire_sample()
        # Apply noise+phase correction before primary calibration
        process_request = ProcessMeasurementRequest(measurement=primary_measurement_raw)
        process_response = self._service.process_measurement(process_request)
        primary_measurement = process_response.processed_measurement
        primary_request = CalibratePrimaryRequest(
            reference_measurement=primary_measurement,
            position=target_position,
            excitation=excitation_params
        )
        self._service.calibrate_primary(primary_request)
        
        # Return complete reference
        reference = self._service.get_reference()
        if reference is None:
            raise RuntimeError("Automatic calibration failed: no reference created")
        return reference
    
    # ========================================================================
    # API Methods - Reference Management
    # ========================================================================
    
    def get_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Get current calibration reference.
        
        Returns:
            Current VoltageMeasurementReference or None
        """
        return self._service.get_reference()
    
    def get_current_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Alias for get_reference() for backward compatibility.
        
        Returns:
            Current VoltageMeasurementReference or None
        """
        return self.get_reference()
    
    def set_reference(self, reference: VoltageMeasurementReference) -> None:
        """
        Set calibration reference.
        
        Args:
            reference: VoltageMeasurementReference to use
        """
        self._service.set_reference(reference)
    
    def reset_calibration(
        self,
        request: ResetCalibrationRequest
    ) -> ResetCalibrationResponse:
        """
        Reset all calibration parameters.
        
        Args:
            request: ResetCalibrationRequest (empty, for API consistency)
        
        Returns:
            ResetCalibrationResponse with success status
        """
        return self._service.reset_calibration(request)
    
    # ========================================================================
    # API Methods - Persistence
    # ========================================================================
    
    def save_reference(
        self,
        name: Optional[str] = None,
        reference: Optional[VoltageMeasurementReference] = None
    ) -> str:
        """
        Save calibration reference to repository.
        
        Args:
            name: Optional name/identifier. If None, generates from timestamp.
            reference: Optional reference to save. If None, uses current reference.
        
        Returns:
            Name/identifier of saved reference
        
        Raises:
            ValueError: If repository not configured or no reference to save
        """
        if self._repository is None:
            raise ValueError("Repository not configured")
        
        if reference is None:
            reference = self._service.get_reference()
            if reference is None:
                raise ValueError("No reference to save. Calibrate first or provide reference.")
        
        return self._repository.save(reference, name)
    
    def load_reference(self, name: str) -> Optional[VoltageMeasurementReference]:
        """
        Load calibration reference from repository.
        
        Args:
            name: Identifier/name of reference to load
        
        Returns:
            VoltageMeasurementReference if found, None otherwise
        
        Raises:
            ValueError: If repository not configured
        """
        if self._repository is None:
            raise ValueError("Repository not configured")
        
        reference = self._repository.load(name)
        if reference is not None:
            self._service.set_reference(reference)
        
        return reference
    
    def load_latest_reference(self) -> Optional[VoltageMeasurementReference]:
        """
        Load most recent calibration reference from repository.
        
        Returns:
            Most recent VoltageMeasurementReference if any exist, None otherwise
        
        Raises:
            ValueError: If repository not configured
        """
        if self._repository is None:
            raise ValueError("Repository not configured")
        
        reference = self._repository.load_latest()
        if reference is not None:
            self._service.set_reference(reference)
        
        return reference
    
    def list_saved_references(self) -> list[str]:
        """
        List all saved reference names.
        
        Returns:
            List of reference names/identifiers
        
        Raises:
            ValueError: If repository not configured
        """
        if self._repository is None:
            raise ValueError("Repository not configured")
        
        return self._repository.list_all()
    
    def delete_reference(self, name: str) -> bool:
        """
        Delete a saved reference.
        
        Args:
            name: Identifier/name of reference to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ValueError: If repository not configured
        """
        if self._repository is None:
            raise ValueError("Repository not configured")
        
        return self._repository.delete(name)
    
    # ========================================================================
    # API Methods - Status/Info
    # ========================================================================
    
    def get_calibration_status(self) -> dict:
        """
        Get current calibration status.
        
        Returns:
            Dict with calibration status information
        """
        reference = self._service.get_reference()
        
        if reference is None or not (reference.is_noise_calibrated() or reference.is_phase_calibrated() or reference.is_primary_calibrated()):
            return {
                "calibrated": False,
                "noise_calibrated": False,
                "phase_calibrated": False,
                "primary_calibrated": False,
            }
        
        return {
            "calibrated": True,
            "noise_calibrated": reference.is_noise_calibrated(),
            "phase_calibrated": reference.is_phase_calibrated(),
            "primary_calibrated": reference.is_primary_calibrated(),
            "calibration_timestamp": reference.calibration_timestamp.isoformat(),
            "calibration_author": reference.calibration_author,
            "calibration_position": (
                {"x": reference.calibration_position.x, "y": reference.calibration_position.y}
                if reference.calibration_position else None
            ),
            "excitation_parameters": (
                {
                    "mode": reference.excitation_parameters.mode.name,
                    "level": reference.excitation_parameters.level.value,
                    "frequency": reference.excitation_parameters.frequency
                }
                if reference.excitation_parameters else None
            ),
        }


# ========================================================================
# Example Usage / Test Script
# ========================================================================

if __name__ == "__main__":
    """
    Example script demonstrating API usage.
    
    This script shows how to use SignalProcessingApiService as a public interface
    for signal processing operations. The API can be used by:
    - View models in the interface layer
    - Integration tests for complete orchestration validation
    """
    print("=== Signal Processing Service API Test ===")
    print()
    
    # Note: In a real scenario, these would be injected from composition root
    # For this example, we show the API structure
    
    print("API Methods available:")
    print("  - process_measurement(measurement)")
    print("  - calibrate_noise(position, excitation)")
    print("  - calibrate_phase(position, excitation)")
    print("  - calibrate_primary(position, excitation)")
    print("  - perform_automatic_calibration(target_position, excitation_params)")
    print("  - get_current_reference()")
    print("  - set_reference(reference)")
    print("  - reset_calibration()")
    print("  - save_reference(name, reference)")
    print("  - load_reference(name)")
    print("  - load_latest_reference()")
    print("  - list_saved_references()")
    print("  - delete_reference(name)")
    print("  - get_calibration_status()")
    print()
    print("To use this API, inject real ports and repository:")
    print("  api = SignalProcessingApiService(")
    print("      acquisition_port=acquisition_port,")
    print("      excitation_port=excitation_port,")
    print("      motion_port=motion_port,")
    print("      repository=repository")
    print("  )")
