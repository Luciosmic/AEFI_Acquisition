"""
Tests unitaires pour CubeVisualizerAdapter.

Valide que l'adapter réagit correctement aux événements (découplage via EventBus).
"""
import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from cube_visualizer_adapter_pyvista import CubeVisualizerAdapter
from cube_visualizer_presenter import CubeVisualizerPresenter
from event_bus import EventBus, Event, EventType
from command_bus import CommandBus


class TestCubeVisualizerAdapter(unittest.TestCase):
    """Tests pour CubeVisualizerAdapter avec découplage EventBus."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois pour tous les tests."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer CommandBus, EventBus, Presenter et Adapter pour chaque test."""
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.presenter = CubeVisualizerPresenter(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        
        # Mock du parent_widget pour éviter de créer un vrai widget Qt
        self.parent_widget = Mock(spec=QWidget)
        
        # Créer l'adapter (sans créer le plotter réel)
        # On mock directement dans _create_plotter_qt
        with patch.object(CubeVisualizerAdapter, '_create_plotter_qt', return_value=None):
            with patch.object(CubeVisualizerAdapter, '_create_plotter_standalone', return_value=None):
                self.adapter = CubeVisualizerAdapter(
                    presenter=self.presenter,
                    event_bus=self.event_bus,
                    parent_widget=None  # Pas de parent pour simplifier
                )
                # Initialiser le plotter comme None pour les tests
                self.adapter.plotter = None
                self.adapter.plotter_widget = None
    
    def test_adapter_subscribes_to_events(self):
        """Test que l'adapter s'abonne aux événements EventBus."""
        # Vérifier que l'adapter s'est abonné
        # (On ne peut pas vérifier directement, mais on peut vérifier qu'il réagit)
        self.assertIsNotNone(self.adapter.event_bus)
        self.assertEqual(self.adapter.event_bus, self.event_bus)
    
    def test_adapter_reacts_to_angles_changed_event(self):
        """Test que l'adapter réagit à l'événement ANGLES_CHANGED."""
        # Mock update_view pour vérifier qu'il est appelé
        self.adapter.update_view = Mock()
        
        # Publier un événement
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 10.0, 'theta_y': 20.0, 'theta_z': 30.0}
        )
        self.event_bus.publish(event)
        
        # Attendre que le signal soit traité
        QApplication.processEvents()
        
        # Vérifier que update_view a été appelé
        self.adapter.update_view.assert_called_once_with(10.0, 20.0, 30.0)
    
    def test_adapter_reacts_to_camera_view_changed_event(self):
        """Test que l'adapter réagit à l'événement CAMERA_VIEW_CHANGED."""
        # Mock reset_camera_view pour vérifier qu'il est appelé
        self.adapter.reset_camera_view = Mock()
        
        # Publier un événement
        event = Event(
            event_type=EventType.CAMERA_VIEW_CHANGED,
            data={'view_name': 'xy'}
        )
        self.event_bus.publish(event)
        
        # Attendre que le signal soit traité
        QApplication.processEvents()
        
        # Vérifier que reset_camera_view a été appelé
        self.adapter.reset_camera_view.assert_called_once_with('xy')
    
    def test_adapter_decoupled_from_presenter(self):
        """Test que l'adapter est découplé du presenter (communication uniquement via EventBus)."""
        # L'adapter ne devrait pas appeler directement les méthodes du presenter
        # pour les modifications d'état (seulement pour les queries)
        
        # Mock les méthodes du presenter
        self.presenter.update_angles = Mock()
        
        # Publier un événement (simule une commande qui a été traitée)
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': 5.0, 'theta_y': 10.0, 'theta_z': 15.0}
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        
        # Le presenter.update_angles ne devrait PAS être appelé directement
        # (il est appelé via CommandBus, pas par l'adapter)
        # L'adapter utilise seulement get_angles() et get_rotation() (queries)
        self.presenter.update_angles.assert_not_called()


if __name__ == '__main__':
    unittest.main()

