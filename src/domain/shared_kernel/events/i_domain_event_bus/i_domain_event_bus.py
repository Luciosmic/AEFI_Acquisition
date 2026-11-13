from abc import ABC, abstractmethod
from typing import Callable, Any

class IDomainEventBus(ABC):
    """
    Interface for the Domain Event Bus.
    Decouples the domain and application layers from the infrastructure implementation.

    Responsibility:
        - Déclarer `subscribe(event_type: str, handler: Callable)` : enregistrement d'un handler.
        - Déclarer `publish(event_type: str, data: Any)` : diffusion à tous les abonnés.
        - Déclarer `unsubscribe(event_type: str, handler: Callable)` : désabonnement.
        - Déclarer `clear_subscribers(event_type: str = None)` : nettoyage pour les tests.

    Rationale:
        Découpler les producteurs d'événements (agrégats, services) des consommateurs (handlers, presenters) sans dépendance directe. L'interface domain garantit que ni le domain ni l'application ne connaissent `InMemoryEventBus` ou tout autre implémentation.

    Design:
        - **Placé dans `domain/events/`** : c'est une abstraction domain, pas applicative — le domain a le droit d'en dépendre.
        - **`event_type` est une str (lowercase class name)** : convention `type(event).__name__.lower()` utilisée uniformément dans tous les publishers.
        - Implémenté par `InMemoryEventBus` (infrastructure/events/).
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
