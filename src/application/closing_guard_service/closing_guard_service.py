"""Closing guard: refuses to close the application while an acquisition export is open."""

import logging
import threading
from typing import Dict, Tuple

from application.closing_guard_service.dtos.close_decision_dto import CloseDecisionDTO, OpenAcquisitionDTO
from application.closing_guard_service.i_api_closing_guard_service import IApiClosingGuardService
from application.closing_guard_service.ports.i_system_session_guard import ISystemSessionGuard
from domain.shared_kernel.events.acquisition_export_closed.acquisition_export_closed import AcquisitionExportClosed
from domain.shared_kernel.events.acquisition_export_opened.acquisition_export_opened import AcquisitionExportOpened
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)

# What the operating system shows when it asks to shut down during an export.
HOLD_REASON = "Acquisition AEFI en cours : attendre la fin de l'export"


class ClosingGuardService(IApiClosingGuardService):
    """Follows the open acquisition exports from the event bus, answers whether the application may
    close, and holds the system session from the first open export to the last closed one."""

    def __init__(self, event_bus: IDomainEventBus, session_guard: ISystemSessionGuard) -> None:
        self._session_guard = session_guard
        # Events come from the scan loop and the sweep tasks; can_close from the UI thread.
        self._lock = threading.Lock()
        self._open: Dict[Tuple[str, str], OpenAcquisitionDTO] = {}
        event_bus.subscribe("acquisitionexportopened", self._on_export_opened)
        event_bus.subscribe("acquisitionexportclosed", self._on_export_closed)

    def can_close(self) -> CloseDecisionDTO:
        with self._lock:
            open_acquisitions = tuple(self._open.values())
        if open_acquisitions:
            logger.info(
                "ClosingGuard: close refused, acquisition export open. acquisitions=%s",
                [(a.acquisition_kind, a.acquisition_id, a.measured_object) for a in open_acquisitions],
            )
            return CloseDecisionDTO(allowed=False, open_acquisitions=open_acquisitions)
        logger.info("ClosingGuard: close accepted, no acquisition export open.")
        return CloseDecisionDTO(allowed=True)

    def _on_export_opened(self, event: AcquisitionExportOpened) -> None:
        key = (event.acquisition_kind, event.acquisition_id)
        with self._lock:
            if key in self._open:
                logger.info("ClosingGuard: export already followed. Doing nothing. kind=%s id=%s", *key)
                return
            first = not self._open
            self._open[key] = OpenAcquisitionDTO(event.acquisition_kind, event.acquisition_id, event.measured_object)
            if first:
                self._session_guard.hold(HOLD_REASON)
        logger.info("ClosingGuard: export opened. kind=%s id=%s open_exports=%d", *key, len(self._open))

    def _on_export_closed(self, event: AcquisitionExportClosed) -> None:
        key = (event.acquisition_kind, event.acquisition_id)
        with self._lock:
            if self._open.pop(key, None) is None:
                logger.warning("ClosingGuard: closed export was not followed. Doing nothing. kind=%s id=%s", *key)
                return
            last = not self._open
            if last:
                self._session_guard.release()
        logger.info("ClosingGuard: export closed. kind=%s id=%s open_exports=%d", *key, len(self._open))
