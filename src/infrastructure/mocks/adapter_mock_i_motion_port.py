import logging
from typing import List, Optional
import threading
import time
from uuid import uuid4
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.motion_completed.motion_completed import MotionCompleted
from domain.shared_kernel.events.position_updated.position_updated import PositionUpdated
from domain.shared_kernel.events.motion_stopped.motion_stopped import MotionStopped
from domain.shared_kernel.events.emergency_stop_triggered.emergency_stop_triggered import EmergencyStopTriggered

logger = logging.getLogger(__name__)

# Measured on the real bench (Arcus Performax 4EX, 21.8 um/step), port level:
# ArcusAdapter.move_to -> MotionCompleted, t = t0 + max(|dx|, |dy|) / v —
# both axes move together. Source:
# infrastructure/hardware/arcus_performax_4EX/characterization/results/2026-10-01_184301_arcus_motion_timing.json
# ponytail: linear model, acceleration ramp ignored — fast mode overestimates a
# 2.5 mm move by ~0.05 s; switch to a trapezoid if a test needs that precision.
MEASURED_PORT_TIMING = {  # speed mode: (t0_s, speed_mm_s)
    "slow": (0.333, 17.40),
    "medium": (0.422, 32.34),
    "fast": (0.555, 59.86),
}
# The real controller boots at HS=1500 (driver DEFAULT_PARAMS) = medium.
DEFAULT_SPEED_MODE = "medium"


def measured_move_duration_s(start: Position2D, target: Position2D, speed_mode: str) -> float:
    t0, speed_mm_s = MEASURED_PORT_TIMING[speed_mode]
    return t0 + max(abs(target.x - start.x), abs(target.y - start.y)) / speed_mm_s


class MockMotionPort(IMotionPort):
    """
    Mock implementation of IMotionPort for testing.
    Records moves and allows position retrieval.

    Supports event-based architecture when event_bus is provided: a move then
    takes the bench-measured duration for its displacement and speed mode
    (MEASURED_PORT_TIMING), unless `motion_delay_ms` forces a fixed delay —
    kept for logic tests that must stay fast.
    """
    def __init__(self, event_bus: Optional[IDomainEventBus] = None, motion_delay_ms: Optional[float] = None):
        logger.debug("__init__: Mock motion port created at (0,0)")
        self._event_bus = event_bus
        self._motion_delay_ms = motion_delay_ms
        self.move_history: List[Position2D] = []
        self._current_pos = Position2D(0, 0)
        self.last_speed: float | None = None
        self.last_speed_mode: str | None = None
        self._is_moving: bool = False

    def move_to(self, position: Position2D) -> str:
        """
        Move to position. Returns motion_id for event-based synchronization.
        If event_bus is provided, publishes PositionUpdated and MotionCompleted events.
        """
        motion_id = str(uuid4())
        logger.info(f"move_to: Moving to {position} (motion_id={motion_id})")
        
        # Publish position update (is_moving=True) if event_bus available
        if self._event_bus:
            self._event_bus.publish("positionupdated", PositionUpdated(
                position=self._current_pos,
                is_moving=True
            ))
        
        self.move_history.append(position)
        self._is_moving = True
        
        # Simulate motion in background thread (like real hardware)
        if self._event_bus:
            if self._motion_delay_ms is not None:
                delay_s = self._motion_delay_ms / 1000.0
            else:
                delay_s = measured_move_duration_s(
                    self._current_pos, position, self.last_speed_mode or DEFAULT_SPEED_MODE
                )
            threading.Thread(
                target=self._simulate_motion,
                args=(motion_id, position, delay_s),
                daemon=True
            ).start()
        else:
            # Synchronous (legacy mode, no events)
            self._current_pos = position
            self._is_moving = False
            logger.info(f"move_to: Arrived at {self._current_pos}")
        
        return motion_id
    
    def _simulate_motion(self, motion_id: str, target: Position2D, delay_s: float):
        """Simulate motion with delay and publish MotionCompleted event."""
        start_time = time.time()
        time.sleep(delay_s)
        
        # Update position
        self._current_pos = target
        self._is_moving = False
        
        duration = (time.time() - start_time) * 1000

        logger.info(f"move_to: Arrived at {self._current_pos} (took {duration:.1f}ms)")
        
        # Publish MotionCompleted and PositionUpdated
        if self._event_bus:
            self._event_bus.publish("motioncompleted", MotionCompleted(
                motion_id=motion_id,
                final_position=target,
                duration_ms=duration
            ))
            self._event_bus.publish("positionupdated", PositionUpdated(
                position=target,
                is_moving=False
            ))

    def get_current_position(self) -> Position2D:
        # ponytail: no per-call log here — a polling getter, LDD's "raw
        # granularity" the same way a register read would be.
        return self._current_pos

    def is_moving(self) -> bool:
        return self._is_moving

    def wait_until_stopped(self) -> None:
        pass  # mock is always stopped between calls

    def set_speed(self, speed: float) -> None:
        # ponytail: recorded only, the timing model is keyed by speed mode —
        # model a custom speed if a caller ever relies on set_speed().
        self.last_speed = speed
        logger.info(f"set_speed: Speed set to {speed} cm/s")

    def set_microns_per_pulse(self, microns_per_pulse: float) -> None:
        # ponytail: recorded only — this mock works in mm and never refuses to
        # move without it (unlike ArcusAdapter); the real refusal is tested
        # on ArcusAdapter over the fake controller.
        self.microns_per_pulse = microns_per_pulse
        logger.info(f"set_microns_per_pulse: {microns_per_pulse} µm/pulse")

    def get_cruise_speed_mm_s(self) -> float:
        return MEASURED_PORT_TIMING[self.last_speed_mode or DEFAULT_SPEED_MODE][1]

    def set_speed_mode(self, mode: str) -> None:
        if mode not in MEASURED_PORT_TIMING:
            raise ValueError(f"Unknown speed mode: {mode}")
        self.last_speed_mode = mode
        logger.info(f"set_speed_mode: Speed mode set to {mode}")

    def stop(self) -> None:
        """Regular stop with deceleration."""
        self._is_moving = False
        logger.info("stop: Normal Stop triggered (decelerating...)")
        
        # Publish MotionStopped event
        if self._event_bus:
            self._event_bus.publish("motionstopped", MotionStopped(
                reason="user_requested"
            ))

    def emergency_stop(self) -> None:
        """Emergency stop - immediate halt."""
        self._is_moving = False
        logger.warning("emergency_stop: EMERGENCY STOP triggered! (Immediate Halt)")
        
        # Publish EmergencyStopTriggered event
        if self._event_bus:
            self._event_bus.publish("emergencystoptriggered", EmergencyStopTriggered())

    def home(self, axis: str | None = None) -> None:
        axis_print = axis if axis else 'BOTH'
        logger.info(f"home: Homing axis: {axis_print}")
        if axis is None:
            self._current_pos = Position2D(0, 0)
            logger.info("home: Both axes homed to (0,0)")
        elif axis.lower() == 'x':
            self._current_pos = Position2D(0, self._current_pos.y)
            logger.info(f"home: X axis homed to (0,{self._current_pos.y})")
        elif axis.lower() == 'y':
            self._current_pos = Position2D(self._current_pos.x, 0)
            logger.info(f"home: Y axis homed to ({self._current_pos.x},0)")

    def set_reference(self, axis: str, position: float = 0.0) -> None:
        """Set current position as reference."""
        if axis.lower() == 'x':
            self._current_pos = Position2D(position, self._current_pos.y)
        elif axis.lower() == 'y':
            self._current_pos = Position2D(self._current_pos.x, position)
        logger.info(f"set_reference: {axis.upper()} axis set to {position}")

    def get_axis_limits(self) -> tuple[float, float]:
        return (1000.0, 1000.0)
