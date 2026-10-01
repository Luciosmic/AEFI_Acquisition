from typing import Callable, Dict, List, Any
from collections import defaultdict
import logging
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

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
        # Lazy %s formatting: repr(data) is expensive (full dataclass dump)
        # and publish() is the hottest path in the system — must not pay
        # that cost when DEBUG is disabled, unlike an f-string would.
        logger.debug("[InMemoryEventBus] Publishing '%s' with data: %s", event_type, data)

        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            logger.warning("[InMemoryEventBus] No subscribers for event '%s'", event_type)

        self._dispatch(handlers, data, event_type)
        # "*" is the wildcard convention for catch-all subscribers (e.g. the event audit log)
        # that need to see every event without being edited each time a new event type is added.
        self._dispatch(self._subscribers.get("*", []), data, event_type)

    def _dispatch(self, handlers: List[Callable[[Any], None]], data: Any, event_type: str) -> None:
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"[InMemoryEventBus] Error in handler for '{event_type}': {e}", exc_info=True)
    
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
