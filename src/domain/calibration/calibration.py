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
from dataclasses import dataclass, field, replace
from typing import Collection, List, Mapping, Optional, Sequence, Tuple

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
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.calibration.events.sensor_calibration_entry_added.sensor_calibration_entry_added import (
    SensorCalibrationEntryAdded,
)
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.calibration.events.source_geometry_calibration_entry_added.source_geometry_calibration_entry_added import (
    SourceGeometryCalibrationEntryAdded,
)
from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentCharacterized,
    HardwareComponentMounted,
)
from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
    QuantityValue,
)
from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
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
        entry = SourceGeometryCalibrationEntry.single(sphere_diameters, pairwise_distances_ext)
        self._domain_events.append(SourceGeometryCalibrationEntryAdded(entry=entry))
        return entry

    def record_hardware_component_characterization(
        self,
        kind: HardwareComponentKind,
        component_name: HardwareComponentName,
        values: Mapping[str, QuantityValue],
    ) -> HardwareComponentCharacterizationEntry:
        """Record (or complete) the characterization of the component named
        `component_name`; quantities left out are not characterized."""
        entry = HardwareComponentCharacterizationEntry.single(
            component_name, ComponentCharacterization.of(kind, values)
        )
        self._domain_events.append(HardwareComponentCharacterized(entry=entry))
        return entry

    def mount_hardware_component(
        self,
        kind: HardwareComponentKind,
        component_name: HardwareComponentName,
        known_component_names: Collection[HardwareComponentName],
        mounted_component_name: Optional[HardwareComponentName],
    ) -> Optional[HardwareComponentSelection]:
        """A component can only be mounted once characterized (in the
        catalog). Re-mounting the mounted component is a logged no-op: no
        selection, no event. Returns the new selection, or None."""
        if component_name not in known_component_names:
            raise ValueError(
                f"Unknown {kind.value} '{component_name}': record its characterization first"
            )
        if component_name == mounted_component_name:
            logger.info("Calibration: %s '%s' already mounted. Doing nothing.", kind.value, component_name)
            return None
        selection = HardwareComponentSelection.now(kind, component_name)
        self._domain_events.append(
            HardwareComponentMounted(kind=kind, component_name=component_name, mounting_id=selection.mounting_id)
        )
        return selection

    @staticmethod
    def current_mounting(selections: Sequence[HardwareComponentSelection]) -> Optional[HardwareComponentSelection]:
        """The current mounting is the latest selection; None if none ever made."""
        if not selections:
            return None
        return max(selections, key=lambda s: s.selected_at)

    @staticmethod
    def mounted_component_name(selections: Sequence[HardwareComponentSelection]) -> Optional[HardwareComponentName]:
        mounting = Calibration.current_mounting(selections)
        return mounting.component_name if mounting else None

    @staticmethod
    def current_characterization(
        entries: Sequence[HardwareComponentCharacterizationEntry], component_name: Optional[HardwareComponentName]
    ) -> Optional[HardwareComponentCharacterizationEntry]:
        """A component's current characterization is its latest entry (earlier
        ones are its history); None if it has no entry."""
        current = None
        for entry in entries:  # recording order breaks timestamp ties (coarse Windows clock)
            if entry.component_name == component_name and (
                current is None or entry.recorded_at >= current.recorded_at
            ):
                current = entry
        return current

    @staticmethod
    def resolve_current_hardware_signature(
        fallback: HardwareSignature,
        mounted_conditioning_electronics_board: Optional[HardwareComponentName],
        mounted_excitation_electronic_board: Optional[HardwareComponentName],
        mounted_sensor: Optional[HardwareComponentName],
    ) -> HardwareSignature:
        """
        The hardware signature references the components declared mounted
        (selected from the catalog): both boards and the sensor. `fallback`
        (device config template, generic names) only fills a kind nothing is
        mounted for yet — logged as a WARNING: the configuration is then
        incomplete.
        """
        signature = fallback
        if mounted_sensor:
            signature = replace(signature, sensor_name=mounted_sensor)
        else:
            logger.warning(
                "Calibration: no sensor declared mounted — configuration incomplete, using template name '%s'",
                fallback.sensor_name,
            )
        if mounted_conditioning_electronics_board:
            signature = replace(signature, conditioning_electronics_board_name=mounted_conditioning_electronics_board)
        else:
            logger.warning(
                "Calibration: no conditioning electronics board declared mounted — configuration incomplete, "
                "using template name '%s'",
                fallback.conditioning_electronics_board_name,
            )
        if mounted_excitation_electronic_board:
            signature = replace(signature, excitation_electronics_board_name=mounted_excitation_electronic_board)
        else:
            logger.warning(
                "Calibration: no excitation electronic board declared mounted — configuration incomplete, "
                "using template name '%s'",
                fallback.excitation_electronics_board_name,
            )
        logger.info("Calibration: hardware signature resolved: %s", signature)
        return signature

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
