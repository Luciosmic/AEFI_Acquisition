"""
Calibration Aggregate

Responsibility:
- Generic aggregate root for all calibration concerns of the system.
- This iteration: manages the synchronous detection phase compensation
  flag and the append-only registry of calibration entries (via the
  repository, not held in memory).
"""

import logging
from uuid import UUID
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.test_bench.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.test_bench_configuration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.test_bench.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.test_bench.calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)
from domain.test_bench.calibration.events.synchronous_detection_phase_calibration_entry_added.synchronous_detection_phase_calibration_entry_added import (
    SynchronousDetectionPhaseCalibrationEntryAdded,
)
from domain.test_bench.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.test_bench.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.test_bench.calibration.events.sensor_calibration_entry_added.sensor_calibration_entry_added import (
    SensorCalibrationEntryAdded,
)
from domain.test_bench.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.test_bench.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.test_bench.calibration.services.source_frame_solver.source_frame_solver import SourceFrameSolver
from domain.test_bench.calibration.events.source_geometry_calibration_entry_added.source_geometry_calibration_entry_added import (
    SourceGeometryCalibrationEntryAdded,
)
from domain.test_bench.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from domain.test_bench.calibration.events.mechanical_transmission_calibration_entry_added.mechanical_transmission_calibration_entry_added import (
    MechanicalTransmissionCalibrationEntryAdded,
)

logger = logging.getLogger(__name__)



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

    def record_sensor_calibration_entry(
        self,
        sensor_mounting_id: Optional[UUID],
        source_geometry_entry_id: UUID,
        angles: SensorRotationAngles,
    ) -> SensorCalibrationEntry:
        """The mounting angles are measured on a mounted sensor: no sensor
        mounted, no angle calibration."""
        if sensor_mounting_id is None:
            raise ValueError("No sensor mounted: mount the sensor (Capteur tab) before calibrating its mounting angles")
        entry = SensorCalibrationEntry.single(sensor_mounting_id, source_geometry_entry_id, angles)
        self._domain_events.append(SensorCalibrationEntryAdded(entry=entry))
        return entry

    def record_source_geometry_calibration_entry(
        self,
        sphere_diameters: Tuple[CaliperMeasurement, ...],
        pairwise_distances_ext: Tuple[CaliperMeasurement, ...],
    ) -> SourceGeometryCalibrationEntry:
        """Only a geometry the 4 spheres can actually take is recorded:
        SourceGeometryInconsistentError otherwise."""
        entry = SourceGeometryCalibrationEntry.single(sphere_diameters, pairwise_distances_ext)
        SourceFrameSolver.solve(entry)
        self._domain_events.append(SourceGeometryCalibrationEntryAdded(entry=entry))
        return entry

    def record_mechanical_transmission_calibration_entry(
        self,
        motor_mounting_id: Optional[UUID],
        stepper_driver_mounting_id: Optional[UUID],
        microsteps: int,
        driver_current_a: float,
        driver_peak_current_a: float,
        microns_per_pulse: float,
    ) -> MechanicalTransmissionCalibrationEntry:
        """A transmission is set up with a mounted motor and a mounted
        driver: either missing, no transmission."""
        if motor_mounting_id is None:
            raise ValueError("No motor mounted: mount the motor (Moteurs tab) before recording the transmission")
        if stepper_driver_mounting_id is None:
            raise ValueError(
                "No stepper driver mounted: mount the driver (Driver pas à pas tab) before recording the transmission"
            )
        entry = MechanicalTransmissionCalibrationEntry.single(
            motor_mounting_id,
            stepper_driver_mounting_id,
            microsteps,
            driver_current_a,
            driver_peak_current_a,
            microns_per_pulse,
        )
        self._domain_events.append(MechanicalTransmissionCalibrationEntryAdded(entry=entry))
        return entry

    @staticmethod
    def current_mechanical_transmission(
        entries: Sequence[MechanicalTransmissionCalibrationEntry],
        motor_mounting_id: Optional[UUID],
        stepper_driver_mounting_id: Optional[UUID],
    ) -> Optional[MechanicalTransmissionCalibrationEntry]:
        """The current transmission is the latest one set up with the motor
        and driver mounted now: after a swap, the old setting no longer
        holds. None if there is none."""
        current = None
        for entry in entries:  # recording order breaks timestamp ties (coarse Windows clock)
            if (
                entry.motor_mounting_id == motor_mounting_id
                and entry.stepper_driver_mounting_id == stepper_driver_mounting_id
                and (current is None or entry.recorded_at >= current.recorded_at)
            ):
                current = entry
        return current

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
