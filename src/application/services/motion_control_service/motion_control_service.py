import logging
from typing import Optional

from application.services.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.services.motion_control_service.errors.motion_control_error import (
    MotionCommandFailed,
    MotionControlError,
    MotionConversionUnavailable,
)
from application.services.motion_control_service.ports.i_motion_conversion_status_port import (
    IMotionConversionStatusPort,
)
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.motion_control_service.ports.motion_conversion_unavailable_error import (
    MotionConversionUnavailableError,
)
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.operation_result import OperationResult
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.position_updated.position_updated import PositionUpdated
from domain.shared_kernel.events.emergency_stop_triggered.emergency_stop_triggered import EmergencyStopTriggered

logger = logging.getLogger(__name__)


class MotionControlService:
    """
    Service for direct motion control (manual jogging, absolute moves, homing).
    Wraps the IMotionPort and updates the UI via IMotionControlOutputPort.
    Uses event-based position updates instead of polling.
    """

    SPEED_MODES = ("slow", "medium", "fast")

    def __init__(
        self,
        motion_port: IMotionPort,
        event_bus: IDomainEventBus,
        conversion_status: Optional[IMotionConversionStatusPort] = None,
    ):
        self._motion_port = motion_port
        self._event_bus = event_bus
        self._conversion_status = conversion_status
        self._last_target_position: Optional[Position2D] = None

    # ------------------------------------------------------------------ #
    # Calibration state (mm/pulse conversion)
    # ------------------------------------------------------------------ #

    def get_conversion_status(self) -> MotionConversionStatusDTO:
        """Whether the bench can move; if not, what is missing and where to enter it."""
        if self._motion_port.is_conversion_available():
            if self._conversion_status is not None and self._conversion_status.get_status().is_available:
                return self._conversion_status.get_status()
            return MotionConversionStatusDTO(is_available=True)
        if self._conversion_status is not None:
            status = self._conversion_status.get_status()
            if not status.is_available:
                return status
        return MotionConversionStatusDTO(is_available=False, missing_quantity="conversion mm/impulsion")

    def _refusal(self, operation: str) -> Optional[MotionConversionUnavailable]:
        """Typed refusal when the bench is not calibrated; None when it can move."""
        if self._motion_port.is_conversion_available():
            return None
        status = self.get_conversion_status()
        logger.warning("MotionControlService: %s refused — no mm/pulse conversion (%s)", operation, status.missing_quantity)
        return MotionConversionUnavailable(
            operation=operation,
            motor_name=status.motor_name,
            missing_quantity=status.missing_quantity,
            where_to_enter=status.where_to_enter,
        )

    def _failure(self, operation: str, error: Exception) -> OperationResult[None, MotionControlError]:
        """Translate a port exception into the use-case error union."""
        if isinstance(error, MotionConversionUnavailableError):
            status = self.get_conversion_status()
            return OperationResult.fail(MotionConversionUnavailable(
                operation=operation,
                motor_name=status.motor_name,
                missing_quantity=status.missing_quantity,
                where_to_enter=status.where_to_enter,
            ))
        failed = MotionCommandFailed(operation=operation, error_detail=str(error))
        logger.error(failed.message)
        return OperationResult.fail(failed)

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
            logger.warning("Failed to read current position from hardware, falling back to (0.0, 0.0)")
            return Position2D(0.0, 0.0)

    def _update_target(self, new_target: Position2D):
        """Update the last target position."""
        self._last_target_position = new_target

    def _reset_target(self):
        """Reset target tracking (e.g. on stop)."""
        self._last_target_position = None

    def move_relative(self, dx: float, dy: float) -> OperationResult[None, MotionControlError]:
        """Move relative to current position (or last target). Returns Result for explicit error handling."""
        logger.info("Command: move relative dx=%s dy=%s", dx, dy)
        refusal = self._refusal("Move relative")
        if refusal is not None:
            return OperationResult.fail(refusal)
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
            return self._failure("Move relative", e)

    def move_absolute(self, x: float, y: float) -> OperationResult[None, MotionControlError]:
        """Move to absolute position. Returns Result for explicit error handling."""
        logger.info("Command: move absolute x=%s y=%s", x, y)
        refusal = self._refusal("Move absolute")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            target = Position2D(x=x, y=y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Move absolute", e)

    def move_absolute_x(self, target_x: float) -> OperationResult[None, MotionControlError]:
        """Move X axis to absolute position, keeping Y. Returns Result for explicit error handling."""
        logger.info("Command: move absolute X target_x=%s", target_x)
        refusal = self._refusal("Move absolute X")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            current = self._get_reference_position()
            target = Position2D(x=target_x, y=current.y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Move absolute X", e)

    def move_absolute_y(self, target_y: float) -> OperationResult[None, MotionControlError]:
        """Move Y axis to absolute position, keeping X. Returns Result for explicit error handling."""
        logger.info("Command: move absolute Y target_y=%s", target_y)
        refusal = self._refusal("Move absolute Y")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            current = self._get_reference_position()
            target = Position2D(x=current.x, y=target_y)
            
            self._motion_port.move_to(target)
            self._update_target(target)
            
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Move absolute Y", e)

    def home_x(self) -> OperationResult[None, MotionControlError]:
        """Home X axis using hardware homing sequence. Returns Result for explicit error handling."""
        logger.info("Command: home X axis")
        refusal = self._refusal("Home X")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            self._motion_port.home(axis="x")
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Home X", e)

    def home_y(self) -> OperationResult[None, MotionControlError]:
        """Home Y axis using hardware homing sequence. Returns Result for explicit error handling."""
        logger.info("Command: home Y axis")
        refusal = self._refusal("Home Y")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            self._motion_port.home(axis="y")
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Home Y", e)

    def home_xy(self) -> OperationResult[None, MotionControlError]:
        """Home both axes using hardware homing sequence. Returns Result for explicit error handling."""
        logger.info("Command: home X and Y axes")
        refusal = self._refusal("Home XY")
        if refusal is not None:
            return OperationResult.fail(refusal)
        try:
            self._motion_port.home(axis=None)  # None = both axes
            self._reset_target() # Homing invalidates position tracking
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Home XY", e)

    def set_speed_mode(self, mode: str) -> OperationResult[None, MotionControlError]:
        """Apply a named speed preset ('slow', 'medium', 'fast'). Returns Result for explicit error handling."""
        logger.info("Command: set speed mode=%s", mode)
        if mode not in self.SPEED_MODES:
            return OperationResult.fail(MotionCommandFailed(
                operation="Set speed mode", error_detail=f"Invalid speed mode: {mode}. Must be one of {self.SPEED_MODES}"
            ))
        try:
            self._motion_port.set_speed_mode(mode)
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Set speed mode", e)

    def stop(self) -> OperationResult[None, MotionControlError]:
        """Stop motion normally (deceleration). Returns Result for explicit error handling."""
        logger.info("Command: stop (deceleration)")
        try:
            self._motion_port.stop()
            self._reset_target() # Stop invalidates target
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Stop", e)

    def emergency_stop(self) -> OperationResult[None, MotionControlError]:
        """Stop motion immediately (E-Stop). Returns Result for explicit error handling."""
        logger.info("Command: emergency stop (E-Stop)")
        try:
            self._motion_port.emergency_stop()
            self._reset_target() # Stop invalidates target
            self._event_bus.publish("emergencystoptriggered", EmergencyStopTriggered())
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Emergency stop", e)

    def set_reference(self, axis: str, position: float = 0.0) -> OperationResult[None, MotionControlError]:
        """
        Set the current position of the specified axis as a reference (e.g. 0).

        Args:
            axis: 'x' or 'y'
            position: The value to set the current position to (default 0.0)
        """
        logger.info("Command: set reference axis=%s position=%s", axis, position)
        try:
            self._motion_port.set_reference(axis, position)
            self._reset_target() # Reference change invalidates tracking
            return OperationResult.ok(None)
        except Exception as e:
            return self._failure("Set reference", e)

    def get_axis_limits(self) -> tuple[float, float]:
        """Get the maximum travel limits for X and Y axes."""
        try:
            return self._motion_port.get_axis_limits()
        except Exception:
            logger.warning("Failed to read axis limits from hardware, falling back to default (1000.0, 1000.0)")
            return (1000.0, 1000.0) # Default fallback
