import logging
import threading

from application.closing_guard_service.ports.i_system_session_guard import ISystemSessionGuard

logger = logging.getLogger(__name__)


class NullSystemSessionGuard(ISystemSessionGuard):
    """Session guard of a system the application cannot ask: holds nothing, says so in the log."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._holding = False

    def hold(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("a session hold needs a reason the operator can read")
        with self._lock:
            self._holding = True
        logger.info("System session guard not supported on this system: session end and sleep not held. reason=%r", reason)

    def release(self) -> None:
        with self._lock:
            was_holding, self._holding = self._holding, False
        if was_holding:
            logger.info("System session guard released (nothing was held on this system).")
