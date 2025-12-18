from abc import ABC, abstractmethod
from typing import Callable, Any

class IDomainEventBus(ABC):
    """
    Interface for the Domain Event Bus.
    Decouples the domain and application layers from the infrastructure implementation.
    """
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: String identifier for the event
            handler: Callable that accepts the event data
        """
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Any) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: String identifier for the event
            data: Event data
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: String identifier for the event
            handler: The handler to remove
        """
        pass
    
    @abstractmethod
    def clear_subscribers(self, event_type: str = None) -> None:
        """
        Clear all subscribers for a specific event type, or all subscribers.
        
        Args:
            event_type: If provided, clear only this event type. Otherwise, clear all.
        """
        pass
