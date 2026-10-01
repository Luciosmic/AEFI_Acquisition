"""
Event Log Presenter

Bridges EventLogMaintenanceService and the Logs panel's event log row:
size display, and user-confirmed deletion of old sessions.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.event_log_maintenance_service.i_api_event_log_maintenance_service import (
    IApiEventLogMaintenanceService,
)

logger = logging.getLogger(__name__)


class EventLogPresenter(QObject):
    # EventLogSummaryDTO
    summary_updated = Signal(object)
    # EventLogSummaryDTO — the view asks the user, then calls on_purge_confirmed
    purge_confirmation_needed = Signal(object)

    def __init__(self, service: IApiEventLogMaintenanceService):
        super().__init__()
        self._service = service

    @Slot()
    def refresh(self) -> None:
        try:
            self.summary_updated.emit(self._service.get_summary())
        except Exception:
            logger.exception("EventLogPresenter: cannot read the event log size")

    @Slot()
    def on_purge_requested(self) -> None:
        try:
            summary = self._service.get_summary()
        except Exception:
            logger.exception("EventLogPresenter: cannot read the event log size")
            return
        self.summary_updated.emit(summary)
        if summary.expired_session_count == 0:
            logger.info("Journal d'événements : aucune session de plus de %d jours à supprimer.", summary.retention_days)
            return
        self.purge_confirmation_needed.emit(summary)

    @Slot()
    def on_purge_confirmed(self) -> None:
        try:
            result = self._service.delete_expired_sessions()
        except Exception:
            logger.exception("EventLogPresenter: event log deletion failed")
        else:
            logger.info(
                "Journal d'événements : %d session(s) supprimée(s), %.1f Mo libérés.",
                result.deleted_session_count,
                result.freed_bytes / 1024**2,
            )
            if result.not_deleted:
                logger.warning(
                    "Journal d'événements : non supprimée(s), fichier utilisé ailleurs ? %s",
                    ", ".join(result.not_deleted),
                )
        self.refresh()
