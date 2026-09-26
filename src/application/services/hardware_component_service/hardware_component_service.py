import logging
from uuid import UUID
from typing import Any, Dict, List, Mapping, Optional

from application.services.hardware_component_service.dtos.hardware_component_dto import (
    HardwareComponentDTO,
    HardwareComponentKindDTO,
    QuantitySpecDTO,
)
from application.services.hardware_component_service.i_api_hardware_component_service import (
    IApiHardwareComponentService,
)
from domain.calibration.calibration import Calibration
from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

HARDWARE_COMPONENT_CHARACTERIZED_TOPIC = "hardwarecomponentcharacterized"
HARDWARE_COMPONENT_MOUNTED_TOPIC = "hardwarecomponentmounted"

logger = logging.getLogger(__name__)


class HardwareComponentService(IApiHardwareComponentService):
    """
    Application Service des composants matériels du banc (cartes
    électroniques, chip de génération, ADC, microcontrôleur, moteurs) :
    catalogue des composants (nom unique + caractérisation complétable dans
    le temps, chaque grandeur pouvant être « non caractérisée ») et choix du
    composant monté pour chaque type.
    """

    def __init__(self, repository: IHardwareComponentRepository, event_bus: IDomainEventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    # -- commands -----------------------------------------------------------------

    def record_characterization(self, kind_key: str, component_name: str, values: Mapping[str, Any]) -> None:
        kind = HardwareComponentKind(kind_key)
        component_name = HardwareComponentName(component_name)
        logger.info(
            "HardwareComponentService: Command record_characterization kind=%s component_name=%s values=%s",
            kind.value,
            component_name,
            dict(values),
        )
        existing = self._latest_entry_per_component(kind)
        calibration = Calibration()
        entry = calibration.record_hardware_component_characterization(kind, component_name, values)
        if component_name in existing:
            logger.info("HardwareComponentService: completing history of %s '%s'", kind.value, component_name)
        else:
            logger.info("HardwareComponentService: registering new %s '%s'", kind.value, component_name)
        uncharacterized = entry.characterization.uncharacterized()
        if uncharacterized:
            logger.warning(
                "HardwareComponentService: %s '%s' recorded with %s NOT CHARACTERIZED — calibration debt",
                kind.value,
                component_name,
                ", ".join(uncharacterized),
            )
        self._repository.add(entry)
        self._publish(calibration)

    def mount_component(self, kind_key: str, component_name: str) -> None:
        kind = HardwareComponentKind(kind_key)
        component_name = HardwareComponentName(component_name)
        logger.info("HardwareComponentService: Command mount_component kind=%s component_name=%s", kind.value, component_name)
        mounted = self.get_mounted_component_name(kind_key)
        calibration = Calibration()
        selection = calibration.mount_hardware_component(
            kind, component_name, self._latest_entry_per_component(kind).keys(), mounted
        )
        if selection is None:
            return
        self._repository.add_selection(selection)
        if kind in (
            HardwareComponentKind.SENSOR,
            HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD,
            HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD,
        ):
            # ponytail: other services got the hardware signature once at startup — restart applies it;
            # inject a shared signature provider if live module swapping becomes needed.
            logger.warning(
                "HardwareComponentService: mounted %s changed (%s -> %s). Calibrations tagged by hardware "
                "signature (synchronous detection phase) keep the previous one until restart.",
                kind.value,
                mounted,
                component_name,
            )
        self._publish(calibration)

    def _publish(self, calibration: Calibration) -> None:
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)

    # -- queries ------------------------------------------------------------------

    def list_kinds(self) -> List[HardwareComponentKindDTO]:
        return [
            HardwareComponentKindDTO(
                key=kind.value,
                label=kind.label,
                quantities=tuple(QuantitySpecDTO(q.key, q.label, q.unit, q.curve_x_label) for q in kind.quantities),
            )
            for kind in HardwareComponentKind
        ]

    def get_current_mounting_id(self, kind_key: str) -> Optional[UUID]:
        """Identity of the current mounting of that kind (composition root:
        the sensor's mounting is what its angle calibrations reference)."""
        mounting = Calibration.current_mounting(self._repository.find_selections(HardwareComponentKind(kind_key)))
        return mounting.mounting_id if mounting else None

    def get_mounted_component_name(self, kind_key: str) -> Optional[str]:
        """Composition root uses it to build the hardware signature."""
        return Calibration.mounted_component_name(self._repository.find_selections(HardwareComponentKind(kind_key)))

    def list_components(self, kind_key: str) -> List[HardwareComponentDTO]:
        latest = self._latest_entry_per_component(HardwareComponentKind(kind_key))
        return [self._to_dto(latest[name]) for name in sorted(latest)]

    def get_mounted_component(self, kind_key: str) -> Optional[HardwareComponentDTO]:
        kind = HardwareComponentKind(kind_key)
        name = self.get_mounted_component_name(kind_key)
        if name is None:
            logger.warning("HardwareComponentService: no %s declared mounted — configuration incomplete", kind.value)
            return None
        entry = Calibration.current_characterization(self._repository.find_all(kind), name)
        uncharacterized = entry.characterization.uncharacterized()
        if uncharacterized:
            logger.warning(
                "HardwareComponentService: mounted %s '%s' has %s NOT CHARACTERIZED",
                kind.value,
                name,
                ", ".join(uncharacterized),
            )
        return self._to_dto(entry)

    def _latest_entry_per_component(self, kind: HardwareComponentKind) -> Dict[str, HardwareComponentCharacterizationEntry]:
        entries = self._repository.find_all(kind)
        return {
            name: Calibration.current_characterization(entries, name)
            for name in {entry.component_name for entry in entries}
        }

    @staticmethod
    def _to_dto(entry: HardwareComponentCharacterizationEntry) -> HardwareComponentDTO:
        return HardwareComponentDTO(
            kind_key=entry.kind.value,
            component_name=entry.component_name,
            values=dict(entry.characterization.values),
            uncharacterized=tuple(entry.characterization.uncharacterized()),
            recorded_at=entry.recorded_at,
        )
