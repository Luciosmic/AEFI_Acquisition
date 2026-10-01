"""
Fake Arcus Performax 4EX Controller

Responsibility:
- In-memory double of ArcusPerformax4EXController for "mock mode" app runs and tests.
- Same public method surface consumed by ArcusAdapter / ArcusPerformax4EXAdvancedConfigurator.
"""

import threading
import time
from typing import Dict, List, Optional

from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import AxisParams

_SIMULATED_MOVE_DELAY_S = 0.2


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
        self._simulate_move(axis, target=position)

    def move_by(self, axis: str, displacement: float) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        axis = axis.lower()
        if not self._is_homed[axis]:
            raise RuntimeError(f"Axis {axis.upper()} must be homed before movement")
        self._simulate_move(axis, target=self._position[axis] + displacement)

    def stop(self, axis: str, immediate: bool = False) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        self._is_moving[axis.lower()] = False

    def wait_move(self, axis: str, timeout: Optional[float] = None) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        deadline = time.time() + (timeout or 30.0)
        while self._is_moving[axis.lower()] and time.time() < deadline:
            time.sleep(0.01)

    def set_position_reference(self, axis: str, position: float = 0) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        self._position[axis.lower()] = position

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def is_homed(self, axis: str) -> bool:
        return self._is_homed[axis.lower()]

    def is_moving(self, axis: Optional[str] = None) -> bool:
        if not self._connected:
            return False
        if axis is None:
            return self._is_moving["x"] or self._is_moving["y"]
        return self._is_moving[axis.lower()]

    def get_position(self, axis: str) -> float:
        if not self._connected:
            raise RuntimeError("Not connected")
        return self._position[axis.lower()]

    def get_status(self, axis: str) -> List[str]:
        if not self._connected:
            raise RuntimeError("Not connected")
        status = []
        if self._is_homed[axis.lower()]:
            status.append("sw_minus_lim")
        if self._is_moving[axis.lower()]:
            status.append("moving")
        return status

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

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
