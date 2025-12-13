"""
Arcus Motion Adapter - Infrastructure Layer

Responsibility:
- Implement IMotionPort interface for motion control
- Handle motion commands and position queries for Arcus Performax 4EX

Rationale:
- Focused on motion control only (configuration is in arcus_advanced_configuration.py)
- Event-based architecture for position updates

Design (QCS):
- SETUP  : connection lifecycle (enable / disable)
- COMMAND: motion commands (move_to, stop, home, wait_until_stopped)
- QUERY  : read-only state (get_current_position, is_moving)
"""

from typing import Optional, List, Dict, Any
import time
import threading
import queue
from uuid import uuid4
from datetime import datetime
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import MotionStarted, MotionCompleted, MotionFailed, PositionUpdated

from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.value_objects.geometric.position_2d import Position2D
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import (
    ArcusPerformax4EXController,
)
from pathlib import Path


class ArcusAdapter(IMotionPort):
    """
    Infrastructure adapter for Arcus Performax 4EX motor controller.

    QCS separation:
    - SETUP: __init__, connect, disconnect
    - COMMAND: move_to, stop, home, wait_until_stopped
    - QUERY: get_current_position, is_moving
    """
    # ... (rest of ArcusAdapter is unchanged, but I need to be careful with replace_file_content limits)
    # Actually, I should target specific blocks. 

# Let's target the imports and the class definition separately or use multi_replace.


    # ==========================================================================
    # SETUP
    # ==========================================================================

    # ==========================================================================
    # SETUP
    # ==========================================================================

    def __init__(self, event_bus: Optional[IDomainEventBus] = None):
        """
        Initialize adapter.
        
        Args:
            event_bus: Domain event bus for publishing motion events.
        """
        self._event_bus = event_bus
        self._axis_x = "X"
        self._axis_y = "Y"
        self._controller: Optional[ArcusPerformax4EXController] = None
        
        # Async Worker Infrastructure
        self._command_queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

    def set_controller(self, controller: ArcusPerformax4EXController) -> None:
        """Inject controller."""
        self._controller = controller

    def enable(self) -> None:
        """
        Enable the adapter (start worker thread).
        Should be called after controller is connected.
        """
        if not self._controller:
            raise RuntimeError("Cannot enable ArcusAdapter: No controller set")
            
        if not self._controller.is_connected():
             print("[ArcusAdapter] Warning: Enabling adapter but controller reports not connected")

        self._start_worker()

    def disable(self) -> None:
        """
        Disable the adapter (stop worker thread).
        """
        self._stop_worker()

    def _start_worker(self):
        """Start the background worker thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        print("[ArcusAdapter] Worker thread started")

    def _stop_worker(self):
        """Stop the background worker thread."""
        self._running = False
        if self._worker_thread:
            # Unblock queue get if waiting
            self._command_queue.put(("STOP_WORKER", None))
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
            print("[ArcusAdapter] Worker thread stopped")

    def _worker_loop(self):
        """
        Background loop to process motion commands sequentially.
        
        Pattern: Command -> Execute -> Wait for Completion -> Next
        """
        while self._running:
            try:
                # Block until a command is available
                cmd_type, args = self._command_queue.get(timeout=0.5)
                
                if cmd_type == "STOP_WORKER":
                    break
                
                if cmd_type == "MOVE_TO":
                    motion_id, position = args
                    start_time = time.time()
                    try:
                        self._internal_move_to(position)
                        # Give hardware time to update status register
                        time.sleep(0.25) 
                        self._internal_wait_until_stopped()
                        
                        if self._event_bus:
                            duration = (time.time() - start_time) * 1000
                            # CRITICAL: Read ACTUAL position from hardware to ensure truth
                            final_pos = self.get_current_position()
                            
                            self._event_bus.publish("motioncompleted", MotionCompleted(
                                motion_id=motion_id,
                                final_position=final_pos,
                                duration_ms=duration
                            ))
                            # Publish position update
                            self._event_bus.publish("positionupdated", PositionUpdated(
                                position=final_pos,
                                is_moving=False
                            ))
                    except Exception as e:
                        print(f"[ArcusAdapter] Motion failed: {e}")
                        if self._event_bus:
                            self._event_bus.publish("motionfailed", MotionFailed(
                                motion_id=motion_id,
                                error=str(e)
                            ))
                elif cmd_type == "HOME":
                    self._internal_home(args)
                    self._internal_wait_until_stopped()
                    # Auto-set reference to 0 after homing
                    if args is None:
                        self._internal_set_reference(("x", 0.0))
                        self._internal_set_reference(("y", 0.0))
                    else:
                        self._internal_set_reference((args, 0.0))
                elif cmd_type == "SET_REFERENCE":
                    self._internal_set_reference(args)
                
                self._command_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ArcusAdapter] Worker error: {e}")

    def _internal_move_to(self, position: Position2D):
        """Internal synchronous move execution."""
        try:
            # Convert mm to steps
            steps_x = int(position.x * self.STEPS_PER_MM)
            steps_y = int(position.y * self.STEPS_PER_MM)
            
            if self._controller:
                self._controller.move_to(self._axis_x, steps_x)
                self._controller.move_to(self._axis_y, steps_y)
        except Exception as e:
            print(f"[ArcusAdapter] Internal move failed: {e}")

    def _internal_home(self, axis: Optional[str]):
        """Internal synchronous home execution."""
        try:
            if self._controller:
                if axis is None:
                    self._controller.home_both(blocking=True)
                else:
                    self._controller.home(axis, blocking=True)
        except Exception as e:
            print(f"[ArcusAdapter] Internal home failed: {e}")

    def _internal_set_reference(self, args):
        """Internal synchronous set reference."""
        if not self._controller:
            return
        
        axis, position = args
        self._controller.set_position_reference(axis, position)

    def _internal_wait_until_stopped(self, timeout: float = 30.0, poll_interval: float = 0.1):
        """Internal synchronous wait."""
        start_time = time.time()
        while self.is_moving():
            if not self._running: # Abort if worker stopped
                break
            if time.time() - start_time > timeout:
                print(f"[ArcusAdapter] Motion timeout after {timeout}s")
                break
            time.sleep(poll_interval)

    # ==========================================================================
    # COMMANDS
    # ==========================================================================

    # Conversion Constants
    MICRONS_PER_STEP = 43.6
    MM_PER_STEP = MICRONS_PER_STEP / 1000.0  # 0.0436 mm/step
    CM_PER_STEP = MM_PER_STEP / 10.0         # 0.00436 cm/step
    
    STEPS_PER_MM = 1.0 / MM_PER_STEP         # ~22.936 steps/mm
    STEPS_PER_CM = 1.0 / CM_PER_STEP         # ~229.36 steps/cm

    def move_to(self, position: Position2D) -> str:
        """
        COMMAND: Move to the specified 2D position.
        
        Async: Pushes command to worker queue and returns immediately.
        Returns: motion_id
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")

        motion_id = str(uuid4())
        
        if self._event_bus:
            self._event_bus.publish("motionstarted", MotionStarted(
                motion_id=motion_id,
                target_position=position
            ))
            # Publish position update (is_moving=True)
            current_pos = self.get_current_position()
            self._event_bus.publish("positionupdated", PositionUpdated(
                position=current_pos,
                is_moving=True
            ))

        # Push to queue
        self._command_queue.put(("MOVE_TO", (motion_id, position)))
        
        return motion_id

    def stop(self, immediate: bool = False) -> None:
        """
        COMMAND: Stop motion on all axes.

        Args:
            immediate: If True, abrupt stop. If False, gradual deceleration.
        """
        # Clear pending commands
        with self._command_queue.mutex:
            self._command_queue.queue.clear()

        if self._controller:
            self._controller.stop(self._axis_x, immediate=immediate)
            self._controller.stop(self._axis_y, immediate=immediate)

    def emergency_stop(self) -> None:
        """
        COMMAND: Immediately stop any ongoing motion (Hard Stop).
        """
        self.stop(immediate=True)

    def set_speed(self, speed_mm_s: float) -> None:
        """
        COMMAND: Set speed for both axes.
        
        Args:
            speed_mm_s: Target speed (mm/s).
        
        Raises:
            RuntimeError: If not connected.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")
        
        try:
            # Convert mm/s to Hz (steps/s)
            # Speed (mm/s) * Steps/mm = Steps/s (Hz)
            speed_hz = int(speed_mm_s * self.STEPS_PER_MM)
            
            # Clamp to hardware limits (approx 10 to 10000 Hz usually)
            # TODO: Verify max speed with datasheet/user
            speed_hz = max(10, min(speed_hz, 100000))
            
            self._controller.set_speed(speed_hz)
        except Exception as e:
            raise RuntimeError(f"Set speed failed: {e}")

    def home(self, axis: Optional[str] = None) -> None:
        """
        COMMAND: Home the specified axis or both axes.
        
        Async: Pushes command to worker queue and returns immediately.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")

        # Push to queue
        self._command_queue.put(("HOME", axis))

    def set_reference(self, axis: str, position: float = 0.0) -> None:
        """
        COMMAND: Set current position as reference.
        
        Async: Pushes command to worker queue and returns immediately.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")
            
        # Push to queue
        self._command_queue.put(("SET_REFERENCE", (axis, position)))

    def wait_until_stopped(self, timeout: float = 30.0, poll_interval: float = 0.1) -> None:
        """
        COMMAND: Block until motion system has stopped moving.
        Waits for both the command queue to drain AND hardware to stop.

        Args:
            timeout: Maximum time to wait in seconds.
            poll_interval: Time between status checks in seconds.

        Raises:
            RuntimeError: If not connected or timeout exceeded.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")

        start_time = time.time()

        # 1. Wait for all pending/running commands to complete
        while self._command_queue.unfinished_tasks > 0:
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Timeout waiting for command queue after {timeout}s")
            time.sleep(poll_interval)

        # 2. Wait for hardware to report stopped (in case of manual moves/inertia)
        while self.is_moving():
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Motion timeout after {timeout}s")
            time.sleep(poll_interval)

    # ==========================================================================
    # QUERIES
    # ==========================================================================

    def get_current_position(self) -> Position2D:
        """
        QUERY: Get current position of the motion system.

        Returns:
            Current 2D position in domain units (mm).

        Raises:
            RuntimeError: If not connected.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")

        try:
            steps_x = self._controller.get_position(self._axis_x)
            steps_y = self._controller.get_position(self._axis_y)
            
            # Convert steps to mm
            pos_x_mm = steps_x * self.MM_PER_STEP
            pos_y_mm = steps_y * self.MM_PER_STEP
            
            return Position2D(x=pos_x_mm, y=pos_y_mm)
        except Exception as e:
            raise RuntimeError(f"Failed to get position: {e}")

    def is_moving(self) -> bool:
        """
        QUERY: Check if motion system is currently moving.

        Returns:
            True if any axis is moving.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._controller:
            raise RuntimeError("Arcus controller not connected")

        try:
            return self._controller.is_moving(self._axis_x) or self._controller.is_moving(self._axis_y)
        except Exception as e:
            raise RuntimeError(f"Failed to check motion status: {e}")

