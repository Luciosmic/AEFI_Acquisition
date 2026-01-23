"""
Interface: Signal Processing Service API

Defines the contract for the Signal Processing Application Service using specialized DTOs.
"""

from abc import ABC, abstractmethod
from typing import Optional
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
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


class IApiSignalProcessingService(ABC):
    """
    Interface for Signal Processing Service.
    Uses generic Request/Response DTO pattern.
    """

    @abstractmethod
    def set_reference(self, reference: VoltageMeasurementReference) -> None:
        """Directly set the calibration reference."""
        pass

    @abstractmethod
    def get_reference(self) -> Optional[VoltageMeasurementReference]:
        """Get the current calibration reference."""
        pass

    @abstractmethod
    def process_measurement(self, request: ProcessMeasurementRequest) -> ProcessMeasurementResponse:
        """Process a measurement using current calibration."""
        pass

    @abstractmethod
    def calibrate_noise(self, request: CalibrateNoiseRequest) -> CalibrateNoiseResponse:
        """Update noise calibration."""
        pass

    @abstractmethod
    def calibrate_phase(self, request: CalibratePhaseRequest) -> CalibratePhaseResponse:
        """Update phase calibration."""
        pass

    @abstractmethod
    def calibrate_primary(self, request: CalibratePrimaryRequest) -> CalibratePrimaryResponse:
        """Update primary field calibration."""
        pass

    @abstractmethod
    def reset_calibration(self, request: ResetCalibrationRequest) -> ResetCalibrationResponse:
        """Reset all calibration parameters."""
        pass
