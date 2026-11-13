"""
MeasuredObject Presenter

Bridges MeasuredObjectService and every MeasuredObjectSelector (Scan and Continuous
Reading panels): pushes the known measured_objects, forwards "Nouvel objet mesuré…"
registrations, and reports their outcome.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.measured_object_registry.measured_object_service.i_api_measured_object_service import IApiMeasuredObjectService
from application.measured_object_registry.measured_object_service.measured_object_service import MEASURED_OBJECT_REGISTERED_TOPIC
from application.measured_object_registry.measured_object_service.measured_object_service_errors import MeasuredObjectNameBlank
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class MeasuredObjectPresenter(QObject):
    # list of MeasuredObjectDTO, sorted by name
    measured_objects_listed = Signal(object)
    # MeasuredObjectDTO, already_registered
    measured_object_registered = Signal(object, bool)
    # reason shown to the measured_object
    registration_failed = Signal(str)

    def __init__(self, service: IApiMeasuredObjectService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        # Registered from either panel: both lists follow.
        event_bus.subscribe(MEASURED_OBJECT_REGISTERED_TOPIC, lambda _event: self.refresh_state())

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
