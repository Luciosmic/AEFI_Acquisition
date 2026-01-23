"""
Signal Processing Service - Request DTOs

Standardized input structures for the API.
"""
from dataclasses import dataclass
from typing import Optional
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters


@dataclass(frozen=True)
class ProcessMeasurementRequest:
    """Request to process a single voltage measurement."""
    measurement: VoltageMeasurement


@dataclass(frozen=True)
class CalibrateNoiseRequest:
    """Request to calibrate noise using a reference measurement."""
    reference_measurement: VoltageMeasurement
    position: Optional[Position2D] = None
    excitation: Optional[ExcitationParameters] = None


@dataclass(frozen=True)
class CalibratePhaseRequest:
    """Request to calibrate phase using a reference measurement."""
    reference_measurement: VoltageMeasurement
    position: Optional[Position2D] = None
    excitation: Optional[ExcitationParameters] = None


@dataclass(frozen=True)
class CalibratePrimaryRequest:
    """Request to calibrate primary field using a reference measurement."""
    reference_measurement: VoltageMeasurement
    position: Optional[Position2D] = None
    excitation: Optional[ExcitationParameters] = None


@dataclass(frozen=True)
class ResetCalibrationRequest:
    """Request to reset/clear current calibration."""
    pass
