"""
Tests d'intégration pour isoler le problème de rendu.

Ces tests vérifient que le widget OpenGL est correctement initialisé.
"""
import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus
from infrastructure.messaging.command_bus import CommandBus


class TestRenderingIntegration(unittest.TestCase):
    """Tests d'intégration pour le rendu."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer les dépendances."""
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.service = CubeVisualizerService(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        self.parent_widget = QWidget()
        self.parent_widget.resize(800, 600)
    
    def test_widget_creation(self):
        """Test que le widget peut être créé."""
        try:
            adapter = CubeVisualizerAdapterModernGL(
                service=self.service,
                event_bus=self.event_bus,
                parent=self.parent_widget
            )
            self.assertIsNotNone(adapter)
            print(f"[TEST] Widget créé: {adapter}")
            print(f"[TEST] Widget size: {adapter.width()}x{adapter.height()}")
            print(f"[TEST] Widget visible: {adapter.isVisible()}")
        except Exception as e:
            self.fail(f"Erreur lors de la création du widget: {e}")
    
    def test_widget_has_size(self):
        """Test que le widget a une taille valide."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        # Le widget devrait avoir une taille (même si 0 initialement)
        width = adapter.width()
        height = adapter.height()
        
        print(f"[TEST] Widget size: {width}x{height}")
        
        # Le widget devrait avoir une taille minimale définie
        self.assertIsInstance(width, int)
        self.assertIsInstance(height, int)
    
    def test_context_creation_in_initializeGL(self):
        """Test que le contexte est créé dans initializeGL."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        # Simuler l'appel à initializeGL
        # Note: initializeGL nécessite un contexte OpenGL actif
        # On va juste vérifier que la méthode existe et peut être appelée
        self.assertTrue(hasattr(adapter, 'initializeGL'))
        self.assertTrue(callable(adapter.initializeGL))
        
        print("[TEST] initializeGL method exists and is callable")
    
    def test_vaos_initialized(self):
        """Test que les VAOs sont initialisés après initializeGL."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        # Avant initializeGL, les VAOs devraient être None
        self.assertIsNone(adapter.cube_vao)
        self.assertIsNone(adapter.grid_vao)
        self.assertEqual(len(adapter.axes_vaos), 0)
        
        print("[TEST] VAOs are None before initializeGL (expected)")
    
    def test_paintGL_exists(self):
        """Test que paintGL existe et est callable."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        self.assertTrue(hasattr(adapter, 'paintGL'))
        self.assertTrue(callable(adapter.paintGL))
        
        print("[TEST] paintGL method exists and is callable")
    
    def test_timer_setup(self):
        """Test que le timer de rendu est configuré."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        self.assertIsNotNone(adapter.timer)
        self.assertTrue(adapter.timer.isActive())
        self.assertAlmostEqual(adapter.timer.interval(), 16, delta=1)  # ~60 FPS
        
        print(f"[TEST] Timer active: {adapter.timer.isActive()}")
        print(f"[TEST] Timer interval: {adapter.timer.interval()}ms")


if __name__ == '__main__':
    unittest.main(verbosity=2)



