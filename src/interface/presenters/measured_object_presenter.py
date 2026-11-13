"""
MeasuredObject Presenter

Bridges MeasuredObjectService, every MeasuredObjectSelector (Scan, Continuous
Reading, Frequency Sweep panels) and the Objets mesurés panel: pushes the known
measured_objects, forwards registrations, renames and deletions, and reports their outcome.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.measured_object_registry.measured_object_service.i_api_measured_object_service import IApiMeasuredObjectService
from application.measured_object_registry.measured_object_service.measured_object_service import (
    MEASURED_OBJECT_DELETED_TOPIC,
    MEASURED_OBJECT_REGISTERED_TOPIC,
    MEASURED_OBJECT_RENAMED_TOPIC,
)
from application.measured_object_registry.measured_object_service.measured_object_service_errors import (
    MeasuredObjectNameBlank,
    MeasuredObjectNameTaken,
    MeasuredObjectNotFound,
    MeasuredObjectServiceError,
)
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class MeasuredObjectPresenter(QObject):
    # list of MeasuredObjectDTO, sorted by name
    measured_objects_listed = Signal(object)
    # MeasuredObjectDTO, already_registered
    measured_object_registered = Signal(object, bool)
    # reason shown to the operator
    registration_failed = Signal(str)
    # Objets mesurés panel: what was done, or why it was refused
    management_done = Signal(str)
    management_failed = Signal(str)

    def __init__(self, service: IApiMeasuredObjectService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        # Registered, renamed or deleted from any panel: every list follows.
        for topic in (MEASURED_OBJECT_REGISTERED_TOPIC, MEASURED_OBJECT_RENAMED_TOPIC, MEASURED_OBJECT_DELETED_TOPIC):
            event_bus.subscribe(topic, lambda _event: self.refresh_state())

    def refresh_state(self) -> None:
        result = self._service.list_measured_objects()
        if result.is_failure:
            self.registration_failed.emit(f"Objets mesurés indisponibles : {result.error.reason}")
            self.measured_objects_listed.emit([])
            return
        self.measured_objects_listed.emit(result.value)

    @Slot(str)
    def on_register_requested(self, name: str) -> None:
        result = self._service.register_measured_object(name)
        if result.is_failure:
            error = result.error
            reason = error.message if isinstance(error, MeasuredObjectNameBlank) else f"registre indisponible : {error.reason}"
            self.registration_failed.emit(reason)
            return
        registration = result.value
        self.measured_object_registered.emit(registration.measured_object, registration.already_registered)

    @Slot(str, str)
    def on_rename_requested(self, measured_object_id: str, name: str) -> None:
        result = self._service.rename_measured_object(measured_object_id, name)
        if result.is_failure:
            self.management_failed.emit(f"Renommage refusé : {_reason(result.error)}")
            return
        self.management_done.emit(f"Nom enregistré : {result.value.name}")

    @Slot(str)
    def on_delete_requested(self, measured_object_id: str) -> None:
        result = self._service.delete_measured_object(measured_object_id)
        if result.is_failure:
            self.management_failed.emit(f"Suppression refusée : {_reason(result.error)}")
            return
        self.management_done.emit(f"Supprimé du registre : {result.value.name}")


def _reason(error: MeasuredObjectServiceError) -> str:
    if isinstance(error, (MeasuredObjectNameBlank, MeasuredObjectNameTaken, MeasuredObjectNotFound)):
        return error.message
    return f"registre indisponible : {error.reason}"
