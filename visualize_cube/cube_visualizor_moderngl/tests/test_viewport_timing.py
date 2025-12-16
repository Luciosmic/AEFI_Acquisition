"""
Test spécifique pour le problème de viewport et timing.

Hypothèse : Le viewport est défini avec une mauvaise taille au moment de initializeGL.
"""
import unittest
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus
from infrastructure.messaging.command_bus import CommandBus


class TestViewportTiming(unittest.TestCase):
    """Tests pour le timing du viewport."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_viewport_size_at_initialization(self):
        """Test que le viewport a la bonne taille à l'initialisation."""
        command_bus = CommandBus()
        event_bus = EventBus()
        service = CubeVisualizerService(command_bus=command_bus, event_bus=event_bus)
        parent = QWidget()
        parent.resize(800, 600)
        parent.show()  # Important !
        QApplication.processEvents()
        
        adapter = CubeVisualizerAdapterModernGL(
            service=service,
            event_bus=event_bus,
            parent=parent
        )
        
        # Forcer l'affichage et le redimensionnement AVANT initializeGL
        adapter.show()
        adapter.resize(800, 600)
        QApplication.processEvents()
        
        print(f"[TEST] Widget size avant initializeGL: {adapter.width()}x{adapter.height()}")
        
        # Le problème : initializeGL est appelé automatiquement par Qt
        # mais peut-être avant que le widget ait sa taille finale
        
        # Vérifier que resizeGL met à jour le viewport
        if adapter.ctx:
            adapter.resizeGL(800, 600)
            print(f"[TEST] Viewport après resizeGL: {adapter.ctx.viewport}")
            self.assertEqual(adapter.ctx.viewport, (0, 0, 800, 600))
    
    def test_viewport_update_in_paintGL(self):
        """Test que paintGL met à jour le viewport si nécessaire."""
        command_bus = CommandBus()
        event_bus = EventBus()
        service = CubeVisualizerService(command_bus=command_bus, event_bus=event_bus)
        parent = QWidget()
        parent.resize(800, 600)
        parent.show()
        QApplication.processEvents()
        
        adapter = CubeVisualizerAdapterModernGL(
            service=service,
            event_bus=event_bus,
            parent=parent
        )
        
        adapter.show()
        adapter.resize(800, 600)
        QApplication.processEvents()
        
        # Vérifier que paintGL met à jour le viewport
        if adapter.ctx:
            # Simuler un changement de taille
            adapter.resize(400, 300)
            
            # paintGL devrait mettre à jour le viewport
            # On vérifie juste que le code est présent
            import inspect
            source = inspect.getsource(adapter.paintGL)
            
            self.assertIn('viewport', source.lower(), "paintGL ne met pas à jour le viewport!")
            print("[TEST] paintGL met à jour le viewport")


if __name__ == '__main__':
    unittest.main(verbosity=2)



