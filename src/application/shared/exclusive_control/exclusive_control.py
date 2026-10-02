"""
Exclusive Control

See exclusive_control_intention.md.
"""

import logging
import threading
from typing import Callable, List, Optional, Sequence, Tuple

from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)


class ExclusiveControl:
    """Single owner of a shared bench resource (runtime-checked exclusive borrow)."""

    def __init__(self, resource: str, on_changed: Callable[[Optional[str]], None]) -> None:
        """`resource`: readable name, used in refusal messages and logs.
        `on_changed(controller)`: called on every change of owner (None = released)."""
        self._resource = resource
        self._on_changed = on_changed
        self._controller: Optional[str] = None
        self._lock = threading.Lock()

    @property
    def controller(self) -> Optional[str]:
        return self._controller

    def take(self, controller: str) -> OperationResult[None, str]:
        logger.info("ExclusiveControl[%s]: take by '%s'", self._resource, controller)
        with self._lock:
            if self._controller == controller:
                logger.info("ExclusiveControl[%s]: '%s' already controls it. Doing nothing.", self._resource, controller)
                return OperationResult.ok(None)
            if self._controller is not None:
                logger.warning(
                    "ExclusiveControl[%s]: refused to '%s', held by '%s'", self._resource, controller, self._controller
                )
                return OperationResult.fail(f"{self._resource} sous le contrôle de : {self._controller}")
            self._controller = controller
        self._on_changed(controller)
        return OperationResult.ok(None)

    def release(self, controller: str) -> None:
        with self._lock:
            if self._controller != controller:
                logger.debug(
                    "ExclusiveControl[%s]: release by '%s' ignored (owner: %s)", self._resource, controller, self._controller
                )
                return
            self._controller = None
        logger.info("ExclusiveControl[%s]: released by '%s'", self._resource, controller)
        self._on_changed(None)

    def refusal(self, caller: Optional[str], command: str) -> Optional[str]:
        """Refusal message if `caller` (None = by hand) may not modify the resource now."""
        owner = self._controller
        if owner is not None and owner != caller:
            logger.warning(
                "ExclusiveControl[%s]: %s refused (caller=%s, controlled by '%s')", self._resource, command, caller, owner
            )
            return f"{self._resource} sous le contrôle de : {owner}"
        return None


Release = Callable[[], None]


def take_all(
    takes: Sequence[Tuple[Callable[[], OperationResult], Release]]
) -> OperationResult[List[Release], str]:
    """Take several resources, all or nothing: `takes` is a list of
    (take, release); on the first refusal, what was already taken is released
    (reverse order) and the refusal returned. On success, the releases to call
    later (already in reverse order)."""
    releases: List[Release] = []
    for take, release in takes:
        result = take()
        if result.is_failure:
            for taken in releases:
                taken()
            return OperationResult.fail(result.error)
        releases.insert(0, release)
    return OperationResult.ok(releases)
