"""
CommandBus — infrastructure/messaging layer.

Thread-safe command dispatcher backed by Qt signals.
"""
from PySide6.QtCore import QObject, Signal, Qt
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """Supported command types."""
    UPDATE_ANGLES = "update_angles"
    RESET_TO_DEFAULT = "reset_to_default"
    RESET_CAMERA_VIEW = "reset_camera_view"


@dataclass
class Command:
    """Generic command envelope."""
    command_type: CommandType
    data: Dict[str, Any]


class CommandBus(QObject):
    """
    Thread-safe CommandBus using Qt queued signals.

    All handlers are invoked on the main Qt thread.
    """
    command_published = Signal(object)

    def __init__(self):
        super().__init__()
        self._handlers: Dict[CommandType, List[Callable]] = {}
        self.command_published.connect(self._dispatch_command, Qt.QueuedConnection)

    def register_handler(self, command_type: CommandType, handler: Callable[[Command], None]):
        self._handlers.setdefault(command_type, []).append(handler)

    def unregister_handler(self, command_type: CommandType, handler: Callable[[Command], None]):
        if command_type in self._handlers:
            try:
                self._handlers[command_type].remove(handler)
            except ValueError:
                pass

    def send(self, command: Command):
        self.command_published.emit(command)

    def _dispatch_command(self, command: Command):
        for handler in self._handlers.get(command.command_type, []):
            try:
                handler(command)
            except Exception as e:
                import traceback
                print(f"[CommandBus] Error in handler for {command.command_type}: {e}")
                traceback.print_exc()
