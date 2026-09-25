"""
Hardware Component Presenter

Bridges HardwareComponentService and one HardwareComponentPanel tab — one
presenter instance per component kind.
"""

import logging
from typing import Any, Dict

from PySide6.QtCore import QObject, Signal, Slot

from application.services.hardware_component_service.dtos.hardware_component_dto import (
    HardwareComponentKindDTO,
)
from application.services.hardware_component_service.hardware_component_service import (
    HARDWARE_COMPONENT_CHARACTERIZED_TOPIC,
    HARDWARE_COMPONENT_MOUNTED_TOPIC,
)
from application.services.hardware_component_service.i_api_hardware_component_service import (
    IApiHardwareComponentService,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class HardwareComponentPresenter(QObject):
    """Presenter for one hardware component kind's tab."""

    # list of HardwareComponentDTO
    components_listed = Signal(object)
    # HardwareComponentDTO or None (= nothing mounted)
    mounted_component_updated = Signal(object)
    status_message = Signal(str)

    def __init__(self, service: IApiHardwareComponentService, kind: HardwareComponentKindDTO, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self.kind = kind
        event_bus.subscribe(HARDWARE_COMPONENT_CHARACTERIZED_TOPIC, self._on_component_event)
        event_bus.subscribe(HARDWARE_COMPONENT_MOUNTED_TOPIC, self._on_component_event)

    def _on_component_event(self, event) -> None:
        kind = getattr(event, "kind", None) or event.entry.kind
        if kind.value == self.kind.key:
            self.refresh_state()

    def refresh_state(self) -> None:
        self.components_listed.emit(self._service.list_components(self.kind.key))
        self.mounted_component_updated.emit(self._service.get_mounted_component(self.kind.key))

    @Slot(str, object)
    def on_save_requested(self, component_name: str, values: Dict[str, Any]) -> None:
        """values[key] None = not characterized."""
        self._report(
            lambda: self._service.record_characterization(self.kind.key, component_name, values),
            f"{self.kind.label} : caractérisation de '{component_name}' enregistrée",
        )

    @Slot(str)
    def on_mount_requested(self, component_name: str) -> None:
        self._report(
            lambda: self._service.mount_component(self.kind.key, component_name),
            f"{self.kind.label} : '{component_name}' monté",
        )

    def _report(self, action, success_message: str) -> None:
        try:
            action()
            logger.info(success_message)
            self.status_message.emit(success_message)
        except Exception as e:
            message = f"Erreur: {e}"
            logger.error(message)
            self.status_message.emit(message)
