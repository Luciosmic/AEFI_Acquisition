from typing import Optional

from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.value_objects.geometric.position_2d import Position2D
from domain.shared.operation_result import OperationResult
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import PositionUpdated
from domain.events.motion_events import PositionUpdated, EmergencyStopTriggered


class MotionControlService:
    """
    Service for direct motion control (manual jogging, absolute moves, homing).
    Wraps the IMotionPort and updates the UI via IMotionControlOutputPort.
    Uses event-based position updates instead of polling.
    """

    def __init__(self, motion_port: IMotionPort, event_bus: IDomainEventBus):
        self._motion_port = motion_port
        self._event_bus = event_bus
        self._last_target_position: Optional[Position2D] = None

    def _get_reference_position(self) -> Position2D:
        """
        Get the reference position for the next move.
        If a move sequence is in progress, use the last target position.
        Otherwise, use the current hardware position.
        """
        if self._last_target_position is not None:
            return self._last_target_position
        
        try:
            return self._motion_port.get_current_position()
        except Exception:
            # Fallback if hardware read fails (shouldn't happen often)
            return Position2D(0.0, 0.0)

    def _update_target(self, new_target: Position2D):
        """Update the last target position."""
        self._last_target_position = new_target

    def _reset_target(self):
        """Reset target tracking (e.g. on stop)."""
        self._last_target_position = None

    def move_relative(self, dx: float, dy: float) -> OperationResult[None, str]:
        """Move relative to current position (or last target). Returns Result for explicit error handling."""
        try:
            current = self._get_reference_position()
            target_x = current.x + dx
            target_y = current.y + dy
            
            # Clamp to limits
            max_x, max_y = self.get_axis_limits()
            target_x = max(0.0, min(target_x, max_x))
            target_y = max(0.0, min(target_y, max_y))
            
            target = Position2D(x=target_x, y=target_y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move relative failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def move_absolute(self, x: float, y: float) -> OperationResult[None, str]:
        """Move to absolute position. Returns Result for explicit error handling."""
        try:
            target = Position2D(x=x, y=y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def move_absolute_x(self, target_x: float) -> OperationResult[None, str]:
        """Move X axis to absolute position, keeping Y. Returns Result for explicit error handling."""
        try:
            current = self._get_reference_position()
            target = Position2D(x=target_x, y=current.y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute X failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def move_absolute_y(self, target_y: float) -> OperationResult[None, str]:
        """Move Y axis to absolute position, keeping X. Returns Result for explicit error handling."""
        try:
            current = self._get_reference_position()
            target = Position2D(x=current.x, y=target_y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute Y failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_x(self) -> OperationResult[None, str]:
        """Home X axis using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis="x")
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home X failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_y(self) -> OperationResult[None, str]:
        """Home Y axis using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis="y")
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home Y failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_xy(self) -> OperationResult[None, str]:
        """Home both axes using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis=None)  # None = both axes
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home XY failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def stop(self) -> OperationResult[None, str]:
        """Stop motion normally (deceleration). Returns Result for explicit error handling."""
        try:
            self._motion_port.stop()
            self._reset_target() # Stop invalidates target
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Stop failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def emergency_stop(self) -> OperationResult[None, str]:
        """Stop motion immediately (E-Stop). Returns Result for explicit error handling."""
        try:
            self._motion_port.emergency_stop()
            self._reset_target() # Stop invalidates target
            self._event_bus.publish("emergencystoptriggered", EmergencyStopTriggered())
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Emergency stop failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def set_reference(self, axis: str, position: float = 0.0) -> OperationResult[None, str]:
        """
        Set the current position of the specified axis as a reference (e.g. 0).
        
        Args:
            axis: 'x' or 'y'
            position: The value to set the current position to (default 0.0)
        """
        try:
            self._motion_port.set_reference(axis, position)
            self._reset_target() # Reference change invalidates tracking
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Set reference failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def get_axis_limits(self) -> tuple[float, float]:
        """Get the maximum travel limits for X and Y axes."""
        try:
            return self._motion_port.get_axis_limits()
        except Exception:
            return (1000.0, 1000.0) # Default fallback
