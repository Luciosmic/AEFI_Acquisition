from PyQt6.QtCore import QObject, pyqtSignal
from application.services.motion_control_service.motion_control_service import MotionControlService
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import PositionUpdated

class MotionControlPresenter(QObject):
    """
    Presenter for the Motion Control UI.
    Receives UI events and calls Service.
    Receives Service updates and emits Qt signals.
    Handles OperationResult explicitly to prevent UI crashes.
    """

    position_updated = pyqtSignal(float, float) # x, y
    status_updated = pyqtSignal(bool)           # is_moving
    operation_failed = pyqtSignal(str)          # error_message

    def __init__(self):
        super().__init__()
        self._service = None # Injected later or during main setup
        self._event_bus = None

    def set_event_bus(self, event_bus: IDomainEventBus):
        self._event_bus = event_bus

    def start_monitoring(self):
        """Subscribe to position updates."""
        if self._event_bus:
            self._event_bus.subscribe("positionupdated", self._on_position_updated)

    def stop_monitoring(self):
        """Unsubscribe from position updates."""
        if self._event_bus:
            self._event_bus.unsubscribe("positionupdated", self._on_position_updated)

    def _on_position_updated(self, event: PositionUpdated):
        """Handle position update event from domain."""
        self.position_updated.emit(event.position.x, event.position.y)
        self.status_updated.emit(event.is_moving)

    def set_service(self, service: MotionControlService):
        self._service = service
        # Don't start monitoring here - wait for hardware to be connected
        # Monitoring will be started after successful startup

    def shutdown(self):
        """Cleanup resources."""
        self.stop_monitoring()


    # ------------------------------------------------------------------ #
    # UI Commands (Explicit Result Handling)
    # ------------------------------------------------------------------ #
    def move_to_x(self, x: float):
        """Move to absolute X position. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.move_absolute_x(x)
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def move_to_y(self, y: float):
        """Move to absolute Y position. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.move_absolute_y(y)
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def move_relative(self, dx: float, dy: float):
        """Move relative to current position. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.move_relative(dx, dy)
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def go_home_x(self):
        """Home X axis. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.home_x()
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def go_home_y(self):
        """Home Y axis. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.home_y()
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def go_home_xy(self):
        """Home both axes. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.home_xy()
            if result.is_failure:
                self.operation_failed.emit(result.error)
            
    def stop_motion(self):
        """Normal stop. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.stop()
            if result.is_failure:
                self.operation_failed.emit(result.error)

    def emergency_stop(self):
        """Hard stop. Handles OperationResult explicitly."""
        if self._service:
            result = self._service.emergency_stop()
            if result.is_failure:
                self.operation_failed.emit(result.error)
