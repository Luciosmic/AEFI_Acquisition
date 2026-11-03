from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)


@dataclass(frozen=True)
class MechanicalTransmissionCalibrationEntryAdded(DomainEvent):
    """Event emitted when a new motion chain setting (mechanical
    transmission) is recorded in the append-only calibration registry."""

    entry: MechanicalTransmissionCalibrationEntry
