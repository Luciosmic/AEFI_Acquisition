"""Refused promise: a correction stage enabled requires calibration for all 3 axes
(see signal_correction_calibration_missing_error_intention.md)."""

from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)


class SignalCorrectionCalibrationMissingError(ValueError):
    def __init__(self, stage: str, calibration: AefiSignalCorrectionCalibration):
        super().__init__(
            f"Signal correction stage '{stage}' is enabled but calibration is missing for at least one axis"
        )
        self.stage = stage
        self.calibration = calibration
