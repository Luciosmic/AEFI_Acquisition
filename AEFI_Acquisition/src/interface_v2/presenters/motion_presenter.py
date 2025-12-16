"""
Motion Control Presenter - Interface V2

Bridges between MotionControlService (Application) and MotionPanel (UI).
Adapted from interface v1 for PySide6 and new panel architecture.
"""

from PySide6.QtCore import QObject, Signal, Slot
from application.services.motion_control_service.motion_control_service import MotionControlService
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.motion_events import PositionUpdated, MotionCompleted, MotionFailed


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
    jog_enabled_changed = Signal(bool)  # enabled state for jog buttons
    limits_updated = Signal(float, float)  # max_x, max_y

    def __init__(self, service: MotionControlService, event_bus: IDomainEventBus = None):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._is_moving = False  # Track motion state to block jog
        self._max_x: float = 1000.0  # Store limits for center calculation
        self._max_y: float = 1000.0
        
        if self._event_bus:
            self.start_monitoring()
            
    def initialize(self):
        """Initialize presenter state (e.g. fetch limits)."""
        if self._service:
            limits = self._service.get_axis_limits()
            self._update_limits(limits[0], limits[1])
    
    def _update_limits(self, max_x: float, max_y: float):
        """Update stored limits and emit signal."""
        self._max_x = max_x
        self._max_y = max_y
        self.limits_updated.emit(max_x, max_y)

    def start_monitoring(self):
        """Subscribe to position updates and motion events."""
        if self._event_bus:
            self._event_bus.subscribe("positionupdated", self._on_position_updated)
            self._event_bus.subscribe("motioncompleted", self._on_motion_completed)
            self._event_bus.subscribe("motionfailed", self._on_motion_failed)

    def stop_monitoring(self):
        """Unsubscribe from position updates and motion events."""
        if self._event_bus:
            self._event_bus.unsubscribe("positionupdated", self._on_position_updated)
            self._event_bus.unsubscribe("motioncompleted", self._on_motion_completed)
            self._event_bus.unsubscribe("motionfailed", self._on_motion_failed)

    def _on_position_updated(self, event: PositionUpdated):
        """Handle position update event from domain."""
        self.position_updated.emit(event.position.x, event.position.y)
        # Update moving state from event
        if event.is_moving != self._is_moving:
            self._is_moving = event.is_moving
            self.status_updated.emit(event.is_moving)
            self.jog_enabled_changed.emit(not event.is_moving)

    def _on_motion_completed(self, event: MotionCompleted):
        """Handle motion completed event - unlock jog."""
        if self._is_moving:
            self._is_moving = False
            self.status_updated.emit(False)
            self.jog_enabled_changed.emit(True)

    def _on_motion_failed(self, event: MotionFailed):
        """Handle motion failed event - unlock jog."""
        if self._is_moving:
            self._is_moving = False
            self.status_updated.emit(False)
            self.jog_enabled_changed.emit(True)
        self.operation_failed.emit(event.error)

    def shutdown(self):
        """Cleanup resources."""
        self.stop_monitoring()

    # ------------------------------------------------------------------ #
    # UI Commands (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot(float, float)
    def on_jog_requested(self, dx: float, dy: float):
        """Handle jog request from panel. Blocked if motion in progress."""
        if self._is_moving:
            print("[MotionPresenter] Jog blocked: motion in progress")
            return
        
        if self._service:
            # Mark as moving immediately to prevent race conditions
            self._is_moving = True
            self.jog_enabled_changed.emit(False)
            
            result = self._service.move_relative(dx, dy)
            if result.is_failure:
                # Unlock on failure
                self._is_moving = False
                self.jog_enabled_changed.emit(True)
                self.operation_failed.emit(result.error)

    @Slot(str, float)
    def on_move_to_requested(self, axis: str, target: float):
        """Handle absolute move request from panel."""
        if self._service:
            if axis == 'x':
                result = self._service.move_absolute_x(target)
            elif axis == 'y':
                result = self._service.move_absolute_y(target)
            else:
                return
            
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot(float, float)
    def on_move_both_requested(self, target_x: float, target_y: float):
        """Handle absolute move request for both axes."""
        if self._service:
            result = self._service.move_absolute(target_x, target_y)
            if result.is_failure:
                self.operation_failed.emit(result.error)

    @Slot()
    def on_move_to_center_requested(self):
        """Handle move to center request. Calculates center based on stored limits."""
        if self._service:
            center_x = self._max_x / 2.0
            center_y = self._max_y / 2.0
            result = self._service.move_absolute(center_x, center_y)
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
