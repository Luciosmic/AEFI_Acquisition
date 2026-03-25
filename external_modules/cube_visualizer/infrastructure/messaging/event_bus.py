"""
EventBus — infrastructure/messaging layer.

Thread-safe event dispatcher backed by Qt signals.
"""
from PySide6.QtCore import QObject, Signal, Qt
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Supported event types."""
    ANGLES_CHANGED = "angles_changed"
    CAMERA_VIEW_CHANGED = "camera_view_changed"
    RESET_REQUESTED = "reset_requested"


@dataclass
class Event:
    """Generic event envelope."""
    event_type: EventType
    data: Dict[str, Any]


class EventBus(QObject):
    """
    Thread-safe EventBus using Qt queued signals.

    All subscribers are invoked on the main Qt thread.
    """
    event_published = Signal(object)

    def __init__(self):
        super().__init__()
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self.event_published.connect(self._dispatch_event, Qt.QueuedConnection)

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass

    def publish(self, event: Event):
        self.event_published.emit(event)

    def _dispatch_event(self, event: Event):
        for handler in self._subscribers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                import traceback
                print(f"[EventBus] Error in handler for {event.event_type}: {e}")
                traceback.print_exc()
