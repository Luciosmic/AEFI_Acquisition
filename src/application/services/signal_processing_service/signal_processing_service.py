"""
Application Service: Signal Processing Service

Implements IApiSignalProcessingService.
Orchestrates the domain logic for signal correction.
"""

from typing import Optional
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.services.signal_calibration_service import SignalCalibrationService
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


class SignalProcessingService(IApiSignalProcessingService):
    """
    Concrete implementation of Signal Processing Service.
    """

    def __init__(self, initial_reference: Optional[VoltageMeasurementReference] = None):
        self._reference: Optional[VoltageMeasurementReference] = initial_reference
        # If no reference provided, start with empty one? Or keep as None (no correction)?
        # For immutable "with_*" updates to work, we need an initial object if we want to build incrementally.
        if self._reference is None:
            self._reference = VoltageMeasurementReference()

    def set_reference(self, reference: VoltageMeasurementReference) -> None:
        self._reference = reference

    def get_reference(self) -> Optional[VoltageMeasurementReference]:
        return self._reference

    def process_measurement(self, request: ProcessMeasurementRequest) -> ProcessMeasurementResponse:
        """
        Apply corrections: Noise -> Phase -> Primary.
        """
        m = request.measurement
        ref = self._reference

        if ref:
            # 1. Noise Correction
            if ref.is_noise_calibrated() and ref.noise_offset:
                m = m.apply_noise_correction(ref.noise_offset)

            # 2. Phase Correction
            if ref.is_phase_calibrated():
                m = m.apply_phase_correction(ref.phase_angles)

            # 3. Primary Field Correction
            if ref.is_primary_calibrated() and ref.primary_offset:
                m = m.apply_primary_field_correction(ref.primary_offset)

        return ProcessMeasurementResponse(
            processed_measurement=m,
            applied_reference=ref
        )

    def calibrate_noise(self, request: CalibrateNoiseRequest) -> CalibrateNoiseResponse:
        """
        Set the noise offset from the provided measurement.
        """
        # Create a new reference with updated noise offset
        # We start from current reference to preserve other calibrations if they exist
        new_ref = self._reference.with_noise_offset(request.reference_measurement)
        
        # Update context
        new_ref = new_ref.with_calibration_context(request.position, request.excitation)
        
        self._reference = new_ref
        
        return CalibrateNoiseResponse(new_ref, success=True)

    def calibrate_phase(self, request: CalibratePhaseRequest) -> CalibratePhaseResponse:
        """
        Calculate phase angles from the measurement and update reference.
        """
        # Calculate angles using Domain Service
        angles = SignalCalibrationService.calculate_phase_angles(request.reference_measurement)
        
        new_ref = self._reference.with_phase_angles(angles)
        new_ref = new_ref.with_calibration_context(request.position, request.excitation)
        
        self._reference = new_ref
        
        return CalibratePhaseResponse(new_ref, success=True)

    def calibrate_primary(self, request: CalibratePrimaryRequest) -> CalibratePrimaryResponse:
        """
        Set the primary field offset from the provided measurement.
        """
        new_ref = self._reference.with_primary_offset(request.reference_measurement)
        new_ref = new_ref.with_calibration_context(request.position, request.excitation)
        
        self._reference = new_ref
        
        return CalibratePrimaryResponse(new_ref, success=True)

    def reset_calibration(self, request: ResetCalibrationRequest) -> ResetCalibrationResponse:
        """
        Reset to a clean reference.
        """
        self._reference = VoltageMeasurementReference()
        return ResetCalibrationResponse(success=True)
