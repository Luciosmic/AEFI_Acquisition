"""
Motion Control Presenter - Interface V2

Bridges between MotionControlService (Application) and MotionPanel (UI).
Adapted from interface v1 for PySide6 and new panel architecture.
"""

from PySide6.QtCore import QObject, Signal, Slot
from application.services.motion_control_service.motion_control_service import MotionControlService
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import PositionUpdated


class MotionPresenter(QObject):
    """
    Presenter for the Motion Control Panel.
    - Receives UI events (signals from panel) and calls Service
    - Receives domain events and updates panel
    """

    # Signals emitted to the UI
    position_updated = Signal(float, float)  # x, y
    status_updated = Signal(bool)  # is_moving
    operation_failed = Signal(str)  # error_message

    def __init__(self, service: MotionControlService, event_bus: IDomainEventBus = None):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        
        if self._event_bus:
            self.start_monitoring()

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

    def shutdown(self):
        """Cleanup resources."""
        self.stop_monitoring()

    # ------------------------------------------------------------------ #
    # UI Commands (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot(float, float)
    def on_jog_requested(self, dx: float, dy: float):
        """Handle jog request from panel."""
        if self._service:
            result = self._service.move_relative(dx, dy)
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot(float, float)
    def on_move_to_requested(self, x: float, y: float):
        """Handle absolute move request from panel."""
        if self._service:
            # Determine which axis to move based on non-zero values
            if x != 0 and y == 0:
                result = self._service.move_absolute_x(x)
            elif y != 0 and x == 0:
                result = self._service.move_absolute_y(y)
            else:
                # Move both (if service supports it, otherwise move sequentially)
                result_x = self._service.move_absolute_x(x)
                result_y = self._service.move_absolute_y(y)
                result = result_y if result_x.is_success else result_x
            
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot(str)
    def on_home_requested(self, axis: str):
        """Handle home request from panel."""
        if self._service:
            if axis == "x":
                result = self._service.home_x()
            elif axis == "y":
                result = self._service.home_y()
            elif axis == "xy":
                result = self._service.home_xy()
            else:
                return
            
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot()
    def on_stop_requested(self):
        """Handle normal stop request from panel."""
        if self._service:
            result = self._service.stop()
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot()
    def on_estop_requested(self):
        """Handle emergency stop request from panel."""
        if self._service:
            result = self._service.emergency_stop()
            if result.is_failure:
                self.operation_failed.emit(result.error)
