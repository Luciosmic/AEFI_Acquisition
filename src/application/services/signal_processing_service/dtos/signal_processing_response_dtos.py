"""
Signal Processing Service - Response DTOs

Standardized output structures for the API.
"""
from dataclasses import dataclass
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference


@dataclass(frozen=True)
class ProcessMeasurementResponse:
    """Response containing processed measurement."""
    processed_measurement: VoltageMeasurement
    applied_reference: VoltageMeasurementReference  # Traceability: "With what reference was this processed?"


@dataclass(frozen=True)
class CalibrateNoiseResponse:
    """Response for noise calibration."""
    new_reference: VoltageMeasurementReference
    success: bool = True


@dataclass(frozen=True)
class CalibratePhaseResponse:
    """Response for phase calibration."""
    new_reference: VoltageMeasurementReference
    success: bool = True


@dataclass(frozen=True)
class CalibratePrimaryResponse:
    """Response for primary calibration."""
    new_reference: VoltageMeasurementReference
    success: bool = True


@dataclass(frozen=True)
class ResetCalibrationResponse:
    """Response for reset."""
    success: bool = True
