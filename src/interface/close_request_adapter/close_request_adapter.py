"""Brings the two ways the application closes to the closing guard: the operator closing the main
window, and the system asking to end the session (Qt's commitDataRequest)."""

import logging

from application.closing_guard_service.i_api_closing_guard_service import IApiClosingGuardService
from interface.presenters.closing_guard_presenter import ClosingGuardPresenter

logger = logging.getLogger(__name__)


class CloseRequestAdapter:
    def __init__(self, closing_guard: IApiClosingGuardService, presenter: ClosingGuardPresenter) -> None:
        self._closing_guard = closing_guard
        self._presenter = presenter

    def on_window_close(self) -> bool:
        """True: the main window may close. False: it stays open, the operator reads why."""
        logger.info("CloseRequest: main window close requested by the operator.")
        decision = self._closing_guard.can_close()
        if not decision.allowed:
            self._presenter.present_close_refused(decision)
            logger.info("CloseRequest: main window kept open, refusal shown to the operator.")
        return decision.allowed

    def on_session_end_request(self, manager) -> None:
        """Cancel the session end while an export is open; the system shows its own screen."""
        logger.info("CloseRequest: session end requested by the system.")
        decision = self._closing_guard.can_close()
        if decision.allowed:
            logger.info("CloseRequest: session end let through.")
            return
        if not manager.allowsInteraction():
            logger.warning("CloseRequest: the system did not let the application refuse the session end.")
            return
        manager.cancel()
        logger.info("CloseRequest: session end cancelled, acquisition export open.")
