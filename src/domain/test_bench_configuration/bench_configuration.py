"""
Bench Configuration Aggregate

Responsibility:
- Aggregate root of the test bench configuration: which hardware components
  are characterized (catalog) and which are mounted on the bench.
- Holds no persisted state: the repository is authoritative for the catalog
  and the mountings; this root states the rules and emits the events.
"""

import logging
from dataclasses import dataclass, field, replace
from typing import Collection, List, Mapping, Optional, Sequence

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.test_bench_configuration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.test_bench_configuration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.test_bench_configuration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentCharacterized,
    HardwareComponentMounted,
)
from domain.test_bench_configuration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
    QuantityValue,
)
from domain.test_bench_configuration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.test_bench_configuration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.test_bench_configuration.value_objects.hardware_signature.hardware_signature import HardwareSignature

logger = logging.getLogger(__name__)


@dataclass
class BenchConfiguration:
    """
    Aggregate Root for the configuration of the test bench: the hardware
    components that are characterized and the ones mounted on it.
    """

    _domain_events: List[DomainEvent] = field(default_factory=list)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

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
            logger.info("BenchConfiguration: %s '%s' already mounted. Doing nothing.", kind.value, component_name)
            return None
        selection = HardwareComponentSelection.now(kind, component_name)
        self._domain_events.append(
            HardwareComponentMounted(kind=kind, component_name=component_name, mounting_id=selection.mounting_id)
        )
        return selection

    @staticmethod
    def current_mounting(selections: Sequence[HardwareComponentSelection]) -> Optional[HardwareComponentSelection]:
        """The current mounting is the latest selection; None if none ever made."""
        current = None
        for selection in selections:  # recording order breaks timestamp ties (coarse Windows clock)
            if current is None or selection.selected_at >= current.selected_at:
                current = selection
        return current

    @staticmethod
    def mounted_component_name(selections: Sequence[HardwareComponentSelection]) -> Optional[HardwareComponentName]:
        mounting = BenchConfiguration.current_mounting(selections)
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
    def is_component_already_recorded(
        entries: Sequence[HardwareComponentCharacterizationEntry], component_name: HardwareComponentName
    ) -> bool:
        """True if the catalog already holds an entry under that name (recording
        again is allowed — it completes the history — but may be a duplicate typo)."""
        return BenchConfiguration.current_characterization(entries, component_name) is not None

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
                "BenchConfiguration: no sensor declared mounted — configuration incomplete, using template name '%s'",
                fallback.sensor_name,
            )
        if mounted_conditioning_electronics_board:
            signature = replace(signature, conditioning_electronics_board_name=mounted_conditioning_electronics_board)
        else:
            logger.warning(
                "BenchConfiguration: no conditioning electronics board declared mounted — configuration incomplete, "
                "using template name '%s'",
                fallback.conditioning_electronics_board_name,
            )
        if mounted_excitation_electronic_board:
            signature = replace(signature, excitation_electronics_board_name=mounted_excitation_electronic_board)
        else:
            logger.warning(
                "BenchConfiguration: no excitation electronic board declared mounted — configuration incomplete, "
                "using template name '%s'",
                fallback.excitation_electronics_board_name,
            )
        logger.info("BenchConfiguration: hardware signature resolved: %s", signature)
        return signature
