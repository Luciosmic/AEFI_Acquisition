"""AefiSignalCorrectionCalibrationUpdated event (see aefi_signal_correction_calibration_updated_intention.md)."""

from dataclasses import dataclass

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.detection_devices.aefi_device.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)


@dataclass(frozen=True)
class AefiSignalCorrectionCalibrationUpdated(DomainEvent):
    """Emitted whenever the signal correction calibration snapshot changes
    (a calibrate_* command, an enable/disable toggle, or a reset)."""

    calibration: AefiSignalCorrectionCalibration
