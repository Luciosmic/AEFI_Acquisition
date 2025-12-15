"""
Tests unitaires pour EventBus.

Valide le découplage et la communication via événements.
"""
import unittest
import sys
import os
from PySide6.QtWidgets import QApplication

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from event_bus import EventBus, Event, EventType


class TestEventBus(unittest.TestCase):
    """Tests pour EventBus."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois pour tous les tests."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer un EventBus pour chaque test."""
        self.event_bus = EventBus()
        self.received_events = []
    
    def test_subscribe_and_publish_angles_changed(self):
        """Test d'abonnement et publication d'un événement ANGLES_CHANGED."""
        def handler(event: Event):
            self.received_events.append(event)
        
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, handler)
        
        # Publier un événement
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 10.0, 'theta_y': 20.0, 'theta_z': 30.0}
        )
        self.event_bus.publish(event)
        
        # Attendre que le signal soit traité
        QApplication.processEvents()
        
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.received_events[0].data['theta_x'], 10.0)
        self.assertEqual(self.received_events[0].data['theta_y'], 20.0)
        self.assertEqual(self.received_events[0].data['theta_z'], 30.0)
    
    def test_multiple_subscribers(self):
        """Test que plusieurs subscribers peuvent recevoir le même événement."""
        subscriber1_events = []
        subscriber2_events = []
        
        def subscriber1(event: Event):
            subscriber1_events.append(event)
        
        def subscriber2(event: Event):
            subscriber2_events.append(event)
        
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, subscriber1)
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, subscriber2)
        
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 1.0, 'theta_y': 2.0, 'theta_z': 3.0}
        )
        self.event_bus.publish(event)
        
        QApplication.processEvents()
        
        self.assertEqual(len(subscriber1_events), 1)
        self.assertEqual(len(subscriber2_events), 1)
    
    def test_unsubscribe(self):
        """Test de désabonnement."""
        def handler(event: Event):
            self.received_events.append(event)
        
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, handler)
        
        # Publier un événement
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 1.0, 'theta_y': 2.0, 'theta_z': 3.0}
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        self.assertEqual(len(self.received_events), 1)
        
        # Se désabonner
        self.event_bus.unsubscribe(EventType.ANGLES_CHANGED, handler)
        
        # Publier un autre événement
        self.received_events.clear()
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 4.0, 'theta_y': 5.0, 'theta_z': 6.0}
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        
        # Le handler ne devrait plus recevoir l'événement
        self.assertEqual(len(self.received_events), 0)
    
    def test_camera_view_changed_event(self):
        """Test de l'événement CAMERA_VIEW_CHANGED."""
        def handler(event: Event):
            self.received_events.append(event)
        
        self.event_bus.subscribe(EventType.CAMERA_VIEW_CHANGED, handler)
        
        event = Event(
            event_type=EventType.CAMERA_VIEW_CHANGED,
            data={'view_name': 'xy'}
        )
        self.event_bus.publish(event)
        
        QApplication.processEvents()
        
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].data['view_name'], 'xy')


if __name__ == '__main__':
    unittest.main()

