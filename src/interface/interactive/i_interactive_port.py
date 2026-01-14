"""
Interactive Port Interface (ISP)

Base interface for user interaction controllers.
Follows Interface Segregation Principle - small, focused interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from domain.shared.events.i_domain_event_bus import IDomainEventBus


class IInteractivePort(ABC):
    """
    Base interface for interactive controllers.
    
    All controllers:
    - Subscribe to EventBus for domain events
    - Publish commands via CommandBus (or direct service calls)
    - Present updates to user via output ports
    """
    
    @abstractmethod
    def initialize(self, event_bus: IDomainEventBus) -> None:
        """
        Initialize the controller with EventBus.
        Controller subscribes to relevant domain events.
        
        Args:
            event_bus: Domain event bus for subscribing to events
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Cleanup: Unsubscribe from EventBus, release resources.
        """
        pass
    
    @abstractmethod
    def get_controller_name(self) -> str:
        """
        Return the name/identifier of this controller.
        
        Returns:
            Controller name (e.g., "scan", "motion", "acquisition")
        """
        pass


class ICommandHandler(ABC):
    """
    Interface for handling commands (CommandBus pattern).
    Controllers implement this to receive commands.
    """
    
    @abstractmethod
    def handle_command(self, command_type: str, command_data: Dict[str, Any]) -> None:
        """
        Handle a command.
        
        Args:
            command_type: Type of command (e.g., "scan_start", "motion_move")
            command_data: Command payload
        """
        pass


class IEventPublisher(ABC):
    """
    Interface for publishing events to EventBus.
    Controllers implement this to publish user interaction events.
    """
    
    @abstractmethod
    def publish_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Publish an event to EventBus.
        
        Args:
            event_type: Event type identifier
            event_data: Event payload
        """
        pass

