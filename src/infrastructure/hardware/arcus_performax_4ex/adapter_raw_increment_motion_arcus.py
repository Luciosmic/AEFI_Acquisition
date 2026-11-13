"""
Arcus Raw Increment Motion Adapter

See adapter_raw_increment_motion_arcus_intention.md.
"""

import logging
import time
from typing import Callable, TypeVar

from application.test_bench.raw_increment_motion.ports.i_raw_increment_motion_port import (
    IRawIncrementMotionPort,
)
from application.test_bench.raw_increment_motion.ports.raw_increment_motion_error import (
    RawIncrementMotionError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Status polling period of wait_until_stopped: short against a dichotomy probe
# (~1 s), long enough to leave the serial link to the position monitor.
WAIT_POLL_S = 0.02
# Same budget as the driver's own default for a blocking homing.
HOMING_TIMEOUT_S = 120.0


class ArcusRawIncrementMotionAdapter(IRawIncrementMotionPort):
    """IRawIncrementMotionPort over the Arcus Performax 4EX driver (real or fake controller)."""

    def __init__(self, controller) -> None:
        self._controller = controller

    def _call(self, operation: str, axis: str, action: Callable[[], T]) -> T:
        try:
            return action()
        except RawIncrementMotionError:
            raise
        except Exception as error:
            logger.error("ArcusRawIncrementMotion: %s axis=%s failed: %s", operation, axis, error)
            raise RawIncrementMotionError(f"{operation} sur l'axe {axis} : {error}") from error

    def home(self, axis: str) -> None:
        logger.info("ArcusRawIncrementMotion: Command home axis=%s", axis)
        self._call("homing", axis, lambda: self._controller.home(axis.lower(), blocking=True, timeout=HOMING_TIMEOUT_S))

    def set_speed(self, axis: str, increments_per_s: int) -> None:
        logger.info("ArcusRawIncrementMotion: Command set_speed axis=%s hs=%d increments/s", axis, increments_per_s)
        self._call("réglage de vitesse", axis, lambda: self._controller.set_speed(int(increments_per_s), axis=axis.lower()))

    def move_to(self, axis: str, increment: int) -> None:
        logger.debug("ArcusRawIncrementMotion: move_to axis=%s increment=%d", axis, increment)
        self._call("déplacement", axis, lambda: self._controller.move_to(axis.lower(), int(increment)))

    def run_to_positive_limit(self, axis: str) -> None:
        logger.info("ArcusRawIncrementMotion: Command run to + limit switch axis=%s", axis)
        self._call("course vers la butée +", axis, lambda: self._controller.jog(axis.lower(), "+"))

    def is_moving(self, axis: str) -> bool:
        return bool(self._call("lecture d'état", axis, lambda: self._controller.is_moving(axis.lower())))

    def get_position(self, axis: str) -> int:
        return int(round(self._call("lecture de position", axis, lambda: self._controller.get_position(axis.lower()))))

    def is_at_positive_limit(self, axis: str) -> bool:
        return bool(self._call("lecture du fin de course +", axis, lambda: self._controller.is_at_limit(axis.lower(), "+")))

    def stop(self, axis: str) -> None:
        logger.info("ArcusRawIncrementMotion: Command stop axis=%s", axis)
        self._call("arrêt", axis, lambda: self._controller.stop(axis.lower(), immediate=False))

    def wait_until_stopped(self, axis: str, timeout_s: float) -> None:
        # Polls is_moving (one locked query each) instead of the driver's
        # wait_move, which holds the driver lock and would freeze the monitor.
        deadline = time.monotonic() + timeout_s
        while self.is_moving(axis):
            if time.monotonic() > deadline:
                raise RawIncrementMotionError(f"l'axe {axis} bouge encore après {timeout_s:.0f} s")
            time.sleep(WAIT_POLL_S)
