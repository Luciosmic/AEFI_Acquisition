from typing import Dict
from datetime import datetime
from application.services.signal_processing_service.i_api_signal_processing_service import IApiSignalProcessingService
from application.services.signal_processing_service.dtos.signal_processing_request_dtos import (
    ProcessMeasurementRequest,
    CalibrateNoiseRequest,
    CalibratePhaseRequest,
    CalibratePrimaryRequest,
    ResetCalibrationRequest
)
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class SignalPostProcessor:
    """
    Adapter for signal processing in the interface layer.
    
    Converts between Dict format (used by UI) and VoltageMeasurement (domain).
    Delegates processing logic to IApiSignalProcessingService.
    """
    
    def __init__(self, signal_processing_service: IApiSignalProcessingService):
        """
        Initialize signal post processor.
        
        Args:
            signal_processing_service: Service for signal processing operations
        """
        self._signal_processing_service = signal_processing_service

    def process_sample(self, raw_measurement: Dict[str, float]) -> Dict[str, float]:
        """
        Apply enabled corrections to a raw measurement dictionary.
        Expected keys format: "Ux In-Phase", "Ux Quadrature", etc.
        
        Args:
            raw_measurement: Dictionary with measurement data
        
        Returns:
            Dictionary with processed measurement data
        """
        # Convert Dict -> VoltageMeasurement
        measurement = self._dict_to_measurement(raw_measurement)
        
        # Create Request DTO
        request = ProcessMeasurementRequest(measurement=measurement)
        
        # Process using service (returns Response DTO)
        response = self._signal_processing_service.process_measurement(request)
        
        # Convert VoltageMeasurement -> Dict
        return self._measurement_to_dict(response.processed_measurement)

    def calibrate_noise(self, current_sample: Dict[str, float]) -> None:
        """
        Calibrate noise offset using current sample.
        
        Args:
            current_sample: Dictionary with measurement data
        """
        measurement = self._dict_to_measurement(current_sample)
        request = CalibrateNoiseRequest(reference_measurement=measurement)
        self._signal_processing_service.calibrate_noise(request)

    def calibrate_phase(self, current_sample_pre_phase: Dict[str, float]) -> None:
        """
        Calibrate phase alignment using current sample.
        This should be called AFTER noise subtraction but BEFORE primary subtraction.
        
        Args:
            current_sample_pre_phase: Dictionary with measurement data (noise-corrected)
        """
        measurement = self._dict_to_measurement(current_sample_pre_phase)
        request = CalibratePhaseRequest(reference_measurement=measurement)
        self._signal_processing_service.calibrate_phase(request)

    def calibrate_primary(self, current_sample_fully_processed: Dict[str, float]) -> None:
        """
        Calibrate primary field offset using current sample.
        This should be called AFTER noise and phase corrections.
        
        Args:
            current_sample_fully_processed: Dictionary with measurement data (fully processed)
        """
        measurement = self._dict_to_measurement(current_sample_fully_processed)
        request = CalibratePrimaryRequest(reference_measurement=measurement)
        self._signal_processing_service.calibrate_primary(request)
    
    def reset_calibration(self) -> None:
        """Reset all calibrations."""
        request = ResetCalibrationRequest()
        self._signal_processing_service.reset_calibration(request)
    
    def _dict_to_measurement(self, d: Dict[str, float]) -> VoltageMeasurement:
        """
        Convert dictionary format to VoltageMeasurement.
        
        Expected keys: "Ux In-Phase", "Ux Quadrature", etc.
        
        Args:
            d: Dictionary with measurement data
        
        Returns:
            VoltageMeasurement object
        """
        return VoltageMeasurement(
            voltage_x_in_phase=d.get("Ux In-Phase", 0.0),
            voltage_x_quadrature=d.get("Ux Quadrature", 0.0),
            voltage_y_in_phase=d.get("Uy In-Phase", 0.0),
            voltage_y_quadrature=d.get("Uy Quadrature", 0.0),
            voltage_z_in_phase=d.get("Uz In-Phase", 0.0),
            voltage_z_quadrature=d.get("Uz Quadrature", 0.0),
            timestamp=datetime.now()
        )
    
    def _measurement_to_dict(self, m: VoltageMeasurement) -> Dict[str, float]:
        """
        Convert VoltageMeasurement to dictionary format.
        
        Args:
            m: VoltageMeasurement object
        
        Returns:
            Dictionary with measurement data
        """
        return {
            "Ux In-Phase": m.voltage_x_in_phase,
            "Ux Quadrature": m.voltage_x_quadrature,
            "Uy In-Phase": m.voltage_y_in_phase,
            "Uy Quadrature": m.voltage_y_quadrature,
            "Uz In-Phase": m.voltage_z_in_phase,
            "Uz Quadrature": m.voltage_z_quadrature,
        }
