"""AefiCorrectedSample aggregate root (see aefi_corrected_sample_intention.md)."""

from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.errors.signal_correction_calibration_missing_error import (
    SignalCorrectionCalibrationMissingError,
)
from domain.signal_processing.events.aefi_sample_corrected.aefi_sample_corrected import AefiSampleCorrected
from domain.signal_processing.services.aefi_signal_correction_service.aefi_signal_correction_service import (
    AefiSignalCorrectionService,
)
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)

AXES = ("x", "y", "z")


@dataclass
class AefiCorrectedSample:
    acquisition_id: UUID
    sample_index: int
    _measurement: AefiVoltageMeasurement
    _domain_events: List[DomainEvent] = field(default_factory=list)

    @property
    def measurement(self) -> AefiVoltageMeasurement:
        return self._measurement

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    @staticmethod
    def correct(
        raw: AefiVoltageMeasurement,
        calibration: AefiSignalCorrectionCalibration,
        acquisition_id: UUID,
        sample_index: int,
    ) -> "AefiCorrectedSample":
        AefiCorrectedSample._reject_incomplete_calibration(calibration)
        corrected_measurement = AefiSignalCorrectionService.apply(raw, calibration)
        instance = AefiCorrectedSample(acquisition_id, sample_index, corrected_measurement)
        instance._domain_events.append(
            AefiSampleCorrected(
                acquisition_id=acquisition_id,
                sample_index=sample_index,
                sample=corrected_measurement,
            )
        )
        return instance

    @staticmethod
    def _reject_incomplete_calibration(calibration: AefiSignalCorrectionCalibration) -> None:
        if calibration.noise_correction_enabled and any(a not in calibration.noise_offset for a in AXES):
            raise SignalCorrectionCalibrationMissingError("noise", calibration)
        if calibration.phase_correction_enabled and any(a not in calibration.phase_angles for a in AXES):
            raise SignalCorrectionCalibrationMissingError("phase", calibration)
        if calibration.primary_correction_enabled and any(a not in calibration.primary_offset for a in AXES):
            raise SignalCorrectionCalibrationMissingError("primary", calibration)
