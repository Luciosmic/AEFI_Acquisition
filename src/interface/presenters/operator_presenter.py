"""
Operator Presenter

Bridges OperatorService and every OperatorSelector (Scan and Continuous
Reading panels): pushes the known operators, forwards "Nouvel opérateur…"
registrations, and reports their outcome.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.operator_service.i_api_operator_service import IApiOperatorService
from application.services.operator_service.operator_service import OPERATOR_REGISTERED_TOPIC
from application.services.operator_service.operator_service_errors import OperatorNameBlank
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class OperatorPresenter(QObject):
    # list of OperatorDTO, sorted by name
    operators_listed = Signal(object)
    # OperatorDTO, already_registered
    operator_registered = Signal(object, bool)
    # reason shown to the operator
    registration_failed = Signal(str)

    def __init__(self, service: IApiOperatorService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        # Registered from either panel: both lists follow.
        event_bus.subscribe(OPERATOR_REGISTERED_TOPIC, lambda _event: self.refresh_state())

    def refresh_state(self) -> None:
        result = self._service.list_operators()
        if result.is_failure:
            self.registration_failed.emit(f"Opérateurs indisponibles : {result.error.reason}")
            self.operators_listed.emit([])
            return
        self.operators_listed.emit(result.value)

    @Slot(str)
    def on_register_requested(self, name: str) -> None:
        result = self._service.register_operator(name)
        if result.is_failure:
            error = result.error
            reason = error.message if isinstance(error, OperatorNameBlank) else f"registre indisponible : {error.reason}"
            self.registration_failed.emit(reason)
            return
        registration = result.value
        self.operator_registered.emit(registration.operator, registration.already_registered)
