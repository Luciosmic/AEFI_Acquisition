from typing import Callable, Dict, List, Any
from collections import defaultdict
import logging
from domain.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)

class InMemoryEventBus(IDomainEventBus):
    """
    In-memory implementation of the Domain Event Bus.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        logger.debug(f"[InMemoryEventBus] Subscribing to '{event_type}'")
        self._subscribers[event_type].append(handler)
    
    def publish(self, event_type: str, data: Any) -> None:
        logger.debug(f"[InMemoryEventBus] Publishing '{event_type}' with data: {data}")
        
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            logger.warning(f"[InMemoryEventBus] No subscribers for event '{event_type}'")
        
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"[InMemoryEventBus] Error in handler for '{event_type}': {e}", exc_info=True)
                print(f"[InMemoryEventBus] Error in handler for '{event_type}': {e}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"[InMemoryEventBus] Unsubscribed from '{event_type}'")
            except ValueError:
                logger.warning(f"[InMemoryEventBus] Handler not found for '{event_type}'")
    
    def clear_subscribers(self, event_type: str = None) -> None:
        if event_type:
            self._subscribers[event_type].clear()
            logger.debug(f"[InMemoryEventBus] Cleared subscribers for '{event_type}'")
        else:
            self._subscribers.clear()
            logger.debug("[InMemoryEventBus] Cleared all subscribers")
