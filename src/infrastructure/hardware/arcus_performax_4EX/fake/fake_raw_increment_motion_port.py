"""
Fake Raw Increment Motion Port

See fake_raw_increment_motion_port_intention.md.
"""

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from application.services.bar_transmission_calibration_service.ports.i_raw_increment_motion_port import (
    IRawIncrementMotionPort,
)
from application.services.bar_transmission_calibration_service.ports.raw_increment_motion_error import (
    RawIncrementMotionError,
)
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FAKE_PLUS_LIMIT_INCREMENTS,
)

# Default cruise speed: the "slow" preset HS of ArcusAdapter.SPEED_MODES,
# measured 797.7 increments/s on the bench (fake_arcus_performax4ex_controller).
DEFAULT_SPEED_INCREMENTS_PER_S = 800
WAIT_POLL_S = 0.02


class _RealClock:
    now = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)


@dataclass
class _Axis:
    position: float = 0.0
    speed: float = DEFAULT_SPEED_INCREMENTS_PER_S
    move: Optional[Tuple[float, float, float, float]] = None  # t_start, t_end, start, target


class FakeRawIncrementMotionPort(IRawIncrementMotionPort):
    """In-memory axes moving linearly in (real or virtual) time."""

    def __init__(
        self,
        clock=None,
        plus_limit_increments: int = FAKE_PLUS_LIMIT_INCREMENTS,
        limit_switch_present: bool = True,
        fail_on: Iterable[str] = (),
    ) -> None:
        """`clock`: object with now()/sleep() (FakeClock in tests; real time by default).
        `limit_switch_present=False`: the axis stops at the end of travel but the
        switch never reads active. `fail_on`: method names raising RawIncrementMotionError."""
        self._clock = clock or _RealClock()
        self.plus_limit_increments = plus_limit_increments
        self._limit_switch_present = limit_switch_present
        self._fail_on = set(fail_on)
        self._axes: Dict[str, _Axis] = {"X": _Axis(), "Y": _Axis()}
        self.homed = {"X": False, "Y": False}

    def _check(self, operation: str, axis: str) -> _Axis:
        if operation in self._fail_on:
            raise RawIncrementMotionError(f"{operation} sur l'axe {axis} : échec simulé")
        if axis not in self._axes:
            raise RawIncrementMotionError(f"axe inconnu {axis!r}")
        return self._axes[axis]

    def _settle(self, state: _Axis) -> float:
        if state.move is None:
            return state.position
        t_start, t_end, start, target = state.move
        now = self._clock.now()
        if now >= t_end:
            state.position, state.move = target, None
            return target
        return start + (target - start) * (now - t_start) / (t_end - t_start)

    def _start_move(self, state: _Axis, target: float) -> None:
        start = self._settle(state)
        now = self._clock.now()
        state.move = (now, now + abs(target - start) / state.speed, start, target)
        if target == start:
            state.move = None

    def home(self, axis: str) -> None:
        state = self._check("home", axis)
        state.position, state.move = 0.0, None
        self.homed[axis] = True

    def set_speed(self, axis: str, increments_per_s: int) -> None:
        if increments_per_s <= 0:
            raise RawIncrementMotionError(f"vitesse invalide {increments_per_s}")
        self._check("set_speed", axis).speed = float(increments_per_s)

    def move_to(self, axis: str, increment: int) -> None:
        state = self._check("move_to", axis)
        self._start_move(state, float(increment))

    def run_to_positive_limit(self, axis: str) -> None:
        state = self._check("run_to_positive_limit", axis)
        self._start_move(state, float(self.plus_limit_increments))

    def is_moving(self, axis: str) -> bool:
        state = self._check("is_moving", axis)
        self._settle(state)
        return state.move is not None

    def get_position(self, axis: str) -> int:
        return int(round(self._settle(self._check("get_position", axis))))

    def is_at_positive_limit(self, axis: str) -> bool:
        state = self._check("is_at_positive_limit", axis)
        return self._limit_switch_present and self._settle(state) >= self.plus_limit_increments

    def stop(self, axis: str) -> None:
        state = self._check("stop", axis)
        state.position, state.move = self._settle(state), None

    def wait_until_stopped(self, axis: str, timeout_s: float) -> None:
        deadline = self._clock.now() + timeout_s
        while self.is_moving(axis):
            if self._clock.now() > deadline:
                raise RawIncrementMotionError(f"l'axe {axis} bouge encore après {timeout_s:.0f} s")
            self._clock.sleep(WAIT_POLL_S)
