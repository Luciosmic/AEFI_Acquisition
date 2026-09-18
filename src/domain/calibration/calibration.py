"""
Calibration Aggregate

Responsibility:
- Generic aggregate root for all calibration concerns of the system.
- This iteration: manages the synchronous detection phase compensation
  flag and the append-only registry of calibration entries (via the
  repository, not held in memory).
"""

from dataclasses import dataclass, field
from typing import List

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)
from domain.calibration.events.synchronous_detection_phase_calibration_entry_added.synchronous_detection_phase_calibration_entry_added import (
    SynchronousDetectionPhaseCalibrationEntryAdded,
)


@dataclass
class Calibration:
    """
    Aggregate Root for all calibration concerns.

    Generic on purpose: future calibration types (e.g. sensor gain) add
    their own fields/methods here without renaming this aggregate.
    """

    synchronous_detection_compensation_enabled: bool = False
    _domain_events: List[DomainEvent] = field(default_factory=list)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def set_synchronous_detection_compensation_enabled(self, enabled: bool) -> None:
        """Idempotent: no event emitted if the value is unchanged."""
        if enabled == self.synchronous_detection_compensation_enabled:
            return
        self.synchronous_detection_compensation_enabled = enabled
        self._domain_events.append(SynchronousDetectionCompensationEnabledChanged(enabled=enabled))

    def record_synchronous_detection_phase_entry(
        self,
        hardware_signature: HardwareSignature,
        point: SynchronousDetectionPhaseCalibrationPoint,
    ) -> SynchronousDetectionPhaseCalibrationEntry:
        entry = SynchronousDetectionPhaseCalibrationEntry.single(hardware_signature, point)
        self._domain_events.append(SynchronousDetectionPhaseCalibrationEntryAdded(entry=entry))
        return entry

    @staticmethod
    def reconstitute(synchronous_detection_compensation_enabled: bool) -> "Calibration":
        """
        Rebuild the aggregate from persisted repository state (rehydration).

        Distinct from the default `Calibration()` constructor, which
        represents a brand-new aggregate. Emits NO domain event: this is
        not a business state transition, just a reread of persisted state.
        """
        return Calibration(
            synchronous_detection_compensation_enabled=synchronous_detection_compensation_enabled
        )
