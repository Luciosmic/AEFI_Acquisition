from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)


@dataclass(frozen=True)
class SourceGeometryCalibrationEntryAdded(DomainEvent):
    """Event emitted when a new source geometry calibration entry is
    recorded in the append-only calibration registry."""

    entry: SourceGeometryCalibrationEntry
