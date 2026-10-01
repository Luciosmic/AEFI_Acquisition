"""
Fake Arcus Performax 4EX Controller

Responsibility:
- In-memory double of ArcusPerformax4EXController for "mock mode" app runs and tests.
- Same public method surface consumed by ArcusAdapter / ArcusPerformax4EXAdvancedConfigurator.
"""

import threading
import time
from typing import Dict, List, Optional, Tuple

from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import AxisParams

# Homing only — move_to/move_by follow the measured timing below.
_SIMULATED_MOVE_DELAY_S = 0.2

# Measured on the real bench, controller level (driver command -> axes stopped
# at target): t = t0 + |delta_steps| / speed, per axis, both axes moving
# together. Keyed by the HS (Hz) of the speed presets. Source:
# ../characterization/results/2026-10-01_184301_arcus_motion_timing.json
# (fitted in mm/s at 21.8 um/step, stored here in steps/s: calibration-free).
# ponytail: linear model, acceleration ramp folded into the fit — fast
# (ACC=500 ms) overestimates a 2.5 mm move by ~0.1 s; trapezoid if needed.
_MEASURED_TIMING_BY_HS: Dict[int, Tuple[float, float]] = {  # hs: (t0_s, speed_steps_s)
    800: (0.101, 797.7),    # slow
    1500: (0.188, 1483.0),  # medium
    3000: (0.283, 2639.0),  # fast
}
# HS no preset uses (set_speed with a custom value): medium's t0, nominal HS speed.
_UNMEASURED_T0_S = 0.188


class FakeArcusPerformax4EXController:
    """
    Stands in for ArcusPerformax4EXController with no real DLL/USB device.
    Lets the REAL ArcusAdapter, ArcusPerformaxLifecycleAdapter, and
    ArcusPerformax4EXAdvancedConfigurator run unmodified — only the
    hardware-facing controller is faked, with realistic in-memory state
    (position, homed flags, moving flags, axis params) since — unlike
    MCU_SerialCommunicator — there is no lower transport layer to fake here.
    """

    def __init__(self) -> None:
        self._connected = False
        self._position: Dict[str, float] = {"x": 0.0, "y": 0.0}
        self._is_homed: Dict[str, bool] = {"x": False, "y": False}
        self._is_moving: Dict[str, bool] = {"x": False, "y": False}
        self._axis_params: Dict[str, AxisParams] = {
            "x": AxisParams(ls=10, hs=1500, acc=300, dec=300),
            "y": AxisParams(ls=10, hs=1500, acc=300, dec=300),
        }
        # axis -> (t_start, t_end, start_position, target) of the move in progress
        self._moves: Dict[str, Tuple[float, float, float, float]] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #

    def connect(self, port: Optional[str] = None) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_axis_params(
        self, axis: str, ls: Optional[int] = None, hs: Optional[int] = None,
        acc: Optional[int] = None, dec: Optional[int] = None,
    ) -> Dict[str, int]:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        with self._lock:
            current = self._axis_params[axis]
            self._axis_params[axis] = AxisParams(
                ls=ls if ls is not None else current.ls,
                hs=hs if hs is not None else current.hs,
                acc=acc if acc is not None else current.acc,
                dec=dec if dec is not None else current.dec,
            )
        return self.get_axis_params_dict(axis)

    def get_axis_params_dict(self, axis: str) -> Dict[str, int]:
        if not self._connected:
            raise RuntimeError("Not connected")
        p = self._axis_params[axis.lower()]
        return {"ls": p.ls, "hs": p.hs, "acc": p.acc, "dec": p.dec}

    def get_axis_params(self, axis: str) -> AxisParams:
        if not self._connected:
            raise RuntimeError("Not connected")
        return self._axis_params[axis.lower()]

    def set_speed(self, hs: int, axis: Optional[str] = None) -> None:
        for ax in (["x", "y"] if axis is None else [axis.lower()]):
            self.set_axis_params(ax, hs=hs)

    def set_low_speed(self, ls: int, axis: Optional[str] = None) -> None:
        for ax in (["x", "y"] if axis is None else [axis.lower()]):
            self.set_axis_params(ax, ls=ls)

    def set_acceleration(self, acc: int, axis: Optional[str] = None) -> None:
        for ax in (["x", "y"] if axis is None else [axis.lower()]):
            self.set_axis_params(ax, acc=acc)

    def set_deceleration(self, dec: int, axis: Optional[str] = None) -> None:
        for ax in (["x", "y"] if axis is None else [axis.lower()]):
            self.set_axis_params(ax, dec=dec)

    # ------------------------------------------------------------------ #
    # Commands
    # ------------------------------------------------------------------ #

    def home(self, axis: str, blocking: bool = True, timeout: float = 120.0) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        self._simulate_move(axis, target=0.0, then_home=True)

    def home_both(self, blocking: bool = True, timeout: float = 120.0) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        for axis in ("x", "y"):
            self._simulate_move(axis, target=0.0, then_home=True)

    def set_homed(self, axis: str, value: bool = True) -> None:
        self._is_homed[axis.lower()] = value

    def move_to(self, axis: str, position: float) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        if not self._is_homed[axis]:
            raise RuntimeError(f"Axis {axis.upper()} must be homed before movement")
        self._start_move(axis, target=position)

    def move_by(self, axis: str, displacement: float) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        if not self._is_homed[axis]:
            raise RuntimeError(f"Axis {axis.upper()} must be homed before movement")
        self._start_move(axis, target=self._current_position(axis) + displacement)

    def stop(self, axis: str, immediate: bool = False) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        with self._lock:
            self._position[axis] = self._current_position(axis)
            self._moves.pop(axis, None)
            self._is_moving[axis] = False

    def wait_move(self, axis: str, timeout: Optional[float] = None) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        deadline = time.time() + (timeout or 30.0)
        while self.is_moving(axis) and time.time() < deadline:
            time.sleep(0.01)

    def set_position_reference(self, axis: str, position: float = 0) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        with self._lock:
            self._moves.pop(axis.lower(), None)
            self._position[axis.lower()] = position

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def is_homed(self, axis: str) -> bool:
        return self._is_homed[axis.lower()]

    def is_moving(self, axis: Optional[str] = None) -> bool:
        if not self._connected:
            return False
        axes = ("x", "y") if axis is None else (axis.lower(),)
        with self._lock:
            for ax in axes:
                self._current_position(ax)  # settles a finished move
            return any(self._is_moving[ax] or ax in self._moves for ax in axes)

    def get_position(self, axis: str) -> float:
        if not self._connected:
            raise RuntimeError("Not connected")
        return self._current_position(axis.lower())

    def get_status(self, axis: str) -> List[str]:
        if not self._connected:
            raise RuntimeError("Not connected")
        status = []
        if self._is_homed[axis.lower()]:
            status.append("sw_minus_lim")
        if self.is_moving(axis):
            status.append("moving")
        return status

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _start_move(self, axis: str, target: float) -> None:
        """Non-blocking, like pylablib's move_to: the command returns at once
        and the axis runs for the measured duration (both axes independently,
        hence together when commanded back to back)."""
        with self._lock:
            start = self._current_position(axis)
            hs = self._axis_params[axis].hs
            t0, speed_steps_s = _MEASURED_TIMING_BY_HS.get(hs, (_UNMEASURED_T0_S, float(hs)))
            now = time.monotonic()
            self._moves[axis] = (now, now + t0 + abs(target - start) / speed_steps_s, start, target)

    def _current_position(self, axis: str) -> float:
        """Position now; settles the move once its end time has passed.
        ponytail: linear in time over the whole move (t0 included) — enough
        for live position display and mid-move stop, not a motion profile."""
        with self._lock:
            move = self._moves.get(axis)
            if move is None:
                return self._position[axis]
            t_start, t_end, start, target = move
            now = time.monotonic()
            if now >= t_end:
                self._position[axis] = target
                del self._moves[axis]
                return target
            return start + (target - start) * (now - t_start) / (t_end - t_start)

    def _simulate_move(self, axis: str, target: float, then_home: bool = False) -> None:
        """Synchronous, short-delay move simulation (mirrors the real
        controller's blocking wait_move behavior closely enough for the
        worker/monitor threads in ArcusAdapter to observe realistic state)."""
        self._is_moving[axis] = True
        time.sleep(_SIMULATED_MOVE_DELAY_S)
        self._position[axis] = target
        if then_home:
            self._is_homed[axis] = True
        self._is_moving[axis] = False
