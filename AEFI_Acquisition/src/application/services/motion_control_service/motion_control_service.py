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



    def move_relative(self, dx: float, dy: float) -> OperationResult[None, str]:
        """Move relative to current position. Returns Result for explicit error handling."""
        try:
            current = self._motion_port.get_current_position()
            target = Position2D(x=current.x + dx, y=current.y + dy)
            self._motion_port.move_to(target)
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
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def move_absolute_x(self, target_x: float) -> OperationResult[None, str]:
        """Move X axis to absolute position, keeping Y. Returns Result for explicit error handling."""
        try:
            current = self._motion_port.get_current_position()
            target = Position2D(x=target_x, y=current.y)
            self._motion_port.move_to(target)
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute X failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def move_absolute_y(self, target_y: float) -> OperationResult[None, str]:
        """Move Y axis to absolute position, keeping X. Returns Result for explicit error handling."""
        try:
            current = self._motion_port.get_current_position()
            target = Position2D(x=current.x, y=target_y)
            self._motion_port.move_to(target)
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Move absolute Y failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_x(self) -> OperationResult[None, str]:
        """Home X axis using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis="x")
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home X failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_y(self) -> OperationResult[None, str]:
        """Home Y axis using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis="y")
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home Y failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def home_xy(self) -> OperationResult[None, str]:
        """Home both axes using hardware homing sequence. Returns Result for explicit error handling."""
        try:
            self._motion_port.home(axis=None)  # None = both axes
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Home XY failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def stop(self) -> OperationResult[None, str]:
        """Stop motion normally (deceleration). Returns Result for explicit error handling."""
        try:
            self._motion_port.stop()
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Stop failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)

    def emergency_stop(self) -> OperationResult[None, str]:
        """Stop motion immediately (E-Stop). Returns Result for explicit error handling."""
        try:
            self._motion_port.emergency_stop()
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
            return OperationResult.ok(None)
        except Exception as e:
            error_msg = f"Set reference failed: {str(e)}"
            print(f"[MotionControlService] {error_msg}")
            return OperationResult.fail(error_msg)
