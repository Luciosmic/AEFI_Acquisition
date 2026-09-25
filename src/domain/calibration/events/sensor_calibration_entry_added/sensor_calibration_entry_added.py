from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)


@dataclass(frozen=True)
class SensorCalibrationEntryAdded(DomainEvent):
    """Event emitted when a new sensor calibration entry is recorded
    in the append-only calibration registry."""

    entry: SensorCalibrationEntry
