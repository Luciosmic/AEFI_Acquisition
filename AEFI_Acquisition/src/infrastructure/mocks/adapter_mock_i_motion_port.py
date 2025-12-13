from typing import List, Optional
import threading
import time
from uuid import uuid4
from domain.value_objects.geometric.position_2d import Position2D
from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import MotionStarted, MotionCompleted, PositionUpdated

class MockMotionPort(IMotionPort):
    """
    Mock implementation of IMotionPort for testing.
    Records moves and allows position retrieval.
    All actions print to terminal for explicit visibility.
    
    Supports event-based architecture when event_bus is provided.
    """
    def __init__(self, event_bus: Optional[IDomainEventBus] = None, motion_delay_ms: float = 100.0):
        print("[MockMotionPort] __init__: Mock motion port created at (0,0)")
        self._event_bus = event_bus
        self._motion_delay_ms = motion_delay_ms
        self.move_history: List[Position2D] = []
        self._current_pos = Position2D(0, 0)
        self.last_speed: float | None = None
        self._is_moving: bool = False

    def move_to(self, position: Position2D) -> str:
        """
        Move to position. Returns motion_id for event-based synchronization.
        If event_bus is provided, publishes MotionStarted and MotionCompleted events.
        """
        motion_id = str(uuid4())
        print(f"[MockMotionPort] move_to: Moving to {position} (motion_id={motion_id})")
        
        # Publish MotionStarted if event_bus available
        if self._event_bus:
            self._event_bus.publish("motionstarted", MotionStarted(
                motion_id=motion_id,
                target_position=position
            ))
            # Publish position update (is_moving=True)
            self._event_bus.publish("positionupdated", PositionUpdated(
                position=self._current_pos,
                is_moving=True
            ))
        
        self.move_history.append(position)
        self._is_moving = True
        
        # Simulate motion in background thread (like real hardware)
        if self._event_bus:
            # Async simulation with delay
            threading.Thread(
                target=self._simulate_motion,
                args=(motion_id, position),
                daemon=True
            ).start()
        else:
            # Synchronous (legacy mode, no events)
            self._current_pos = position
            self._is_moving = False
            print(f"[MockMotionPort] move_to: Arrived at {self._current_pos}")
        
        return motion_id
    
    def _simulate_motion(self, motion_id: str, target: Position2D):
        """Simulate motion with delay and publish MotionCompleted event."""
        start_time = time.time()
        time.sleep(self._motion_delay_ms / 1000.0)  # Simulate motion time
        
        # Update position
        self._current_pos = target
        self._is_moving = False
        
        duration = (time.time() - start_time) * 1000
        
        print(f"[MockMotionPort] move_to: Arrived at {self._current_pos} (took {duration:.1f}ms)")
        
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
        print(f"[MockMotionPort] get_current_position: Current position is {self._current_pos}")
        return self._current_pos

    def is_moving(self) -> bool:
        print(f"[MockMotionPort] is_moving: Motion system is {'MOVING' if self._is_moving else 'STOPPED'}")
        return self._is_moving

    def wait_until_stopped(self) -> None:
        print("[MockMotionPort] wait_until_stopped: Waiting for motion to stop (mock is always stopped)")

    def set_speed(self, speed: float) -> None:
        self.last_speed = speed
        print(f"[MockMotionPort] set_speed: Speed set to {speed} cm/s")

    def stop(self, immediate: bool = False) -> None:
        """Mock normal stop."""
        self._is_moving = False
        stop_type = "EMERGENCY" if immediate else "Normal"
        print(f"[MockMotionPort] stop: {stop_type} Stop triggered (decelerating...)")

    def emergency_stop(self) -> None:
        """Mock emergency stop."""
        self._is_moving = False
        print("[MockMotionPort] emergency_stop: EMERGENCY STOP triggered! (Immediate Halt)")

    def home(self, axis: str | None = None) -> None:
        axis_print = axis if axis else 'BOTH'
        print(f"[MockMotionPort] home: Homing axis: {axis_print}")
        if axis is None:
            self._current_pos = Position2D(0, 0)
            print("[MockMotionPort] home: Both axes homed to (0,0)")
        elif axis.lower() == 'x':
            self._current_pos = Position2D(0, self._current_pos.y)
            print(f"[MockMotionPort] home: X axis homed to (0,{self._current_pos.y})")
        elif axis.lower() == 'y':
            self._current_pos = Position2D(self._current_pos.x, 0)
            print(f"[MockMotionPort] home: Y axis homed to ({self._current_pos.x},0)")

    def set_reference(self, axis: str, position: float = 0.0) -> None:
        """Set current position as reference."""
        if axis.lower() == 'x':
            self._current_pos = Position2D(position, self._current_pos.y)
        elif axis.lower() == 'y':
            self._current_pos = Position2D(self._current_pos.x, position)
        print(f"[MockMotionPort] set_reference: {axis.upper()} axis set to {position}")
