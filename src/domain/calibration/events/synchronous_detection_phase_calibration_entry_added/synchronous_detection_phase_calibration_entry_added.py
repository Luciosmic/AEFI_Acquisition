from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)


@dataclass(frozen=True)
class SynchronousDetectionPhaseCalibrationEntryAdded(DomainEvent):
    """Event emitted when a new synchronous detection phase calibration
    entry is recorded in the append-only calibration registry."""

    entry: SynchronousDetectionPhaseCalibrationEntry
