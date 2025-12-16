"""
EventBus minimal pour gérer les événements de manière thread-safe.

Utilise PySide6.QtCore.QObject et Signal pour garantir l'exécution sur le thread principal Qt.
"""
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Types d'événements supportés."""
    ANGLES_CHANGED = "angles_changed"
    CAMERA_VIEW_CHANGED = "camera_view_changed"
    RESET_REQUESTED = "reset_requested"


@dataclass
class Event:
    """Événement générique."""
    event_type: EventType
    data: Dict[str, Any]


class EventBus(QObject):
    """
    EventBus thread-safe utilisant les signaux Qt.
    
    Garantit que tous les handlers sont exécutés sur le thread principal Qt.
    """
    
    # Signal émis quand un événement est publié
    event_published = Signal(object)  # Event
    
    def __init__(self):
        super().__init__()
        self._subscribers: Dict[EventType, List[Callable]] = {}
        # Connecter le signal à un slot qui dispatch les événements
        self.event_published.connect(self._dispatch_event, Qt.QueuedConnection)
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """
        S'abonner à un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction appelée avec l'événement
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """
        Se désabonner d'un type d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Handler à retirer
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event: Event):
        """
        Publier un événement (thread-safe).
        
        Args:
            event: Événement à publier
        """
        # Émettre le signal (thread-safe, sera dispatché sur le thread principal)
        self.event_published.emit(event)
    
    def _dispatch_event(self, event: Event):
        """
        Dispatch l'événement aux subscribers (exécuté sur le thread principal Qt).
        
        Args:
            event: Événement à dispatcher
        """
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[ERROR] Erreur dans handler pour {event.event_type}: {e}")
                    import traceback
                    traceback.print_exc()



