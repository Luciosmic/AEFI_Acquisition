import logging
import threading
from typing import List

from application.closing_guard_service.ports.i_system_session_guard import ISystemSessionGuard

logger = logging.getLogger(__name__)


class FakeNullSystemSessionGuard(ISystemSessionGuard):
    """In-memory session guard: remembers each hold reason and each effective release."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.holds: List[str] = []
        self.releases = 0
        self.is_holding = False

    def hold(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("a session hold needs a reason the operator can read")
        with self._lock:
            self.holds.append(reason)
            self.is_holding = True
        logger.info("Fake system session guard: session end and sleep held. reason=%r", reason)

    def release(self) -> None:
        with self._lock:
            if not self.is_holding:
                return
            self.is_holding = False
            self.releases += 1
        logger.info("Fake system session guard: session end and sleep released.")
