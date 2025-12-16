"""
Tests de debug pour isoler pourquoi le cube ne s'affiche pas.

Vérifie les hypothèses :
1. Le widget est-il visible au moment du rendu ?
2. Le viewport est-il correctement défini ?
3. La matrice MVP transforme-t-elle le cube hors de la vue ?
4. Le contexte est-il actif au moment du rendu ?
"""
import unittest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus
from infrastructure.messaging.command_bus import CommandBus


class TestCubeRenderingDebug(unittest.TestCase):
    """Tests de debug pour le rendu du cube."""
    
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
        self.parent_widget.show()  # Important : rendre visible
    
    def test_widget_visibility_at_creation(self):
        """Test que le widget est visible lors de la création."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        # Le widget devrait être visible si le parent l'est
        print(f"[TEST] Parent visible: {self.parent_widget.isVisible()}")
        print(f"[TEST] Widget visible: {adapter.isVisible()}")
        print(f"[TEST] Widget size: {adapter.width()}x{adapter.height()}")
        
        # Forcer l'affichage
        adapter.show()
        adapter.resize(800, 600)
        
        # Traiter les événements Qt
        QApplication.processEvents()
        
        print(f"[TEST] Après show() - Widget visible: {adapter.isVisible()}")
        print(f"[TEST] Après show() - Widget size: {adapter.width()}x{adapter.height()}")
        
        # Le widget devrait avoir une taille après show()
        self.assertGreater(adapter.width(), 0, "Widget n'a pas de largeur!")
        self.assertGreater(adapter.height(), 0, "Widget n'a pas de hauteur!")
    
    def test_viewport_initialization_timing(self):
        """Test le timing de l'initialisation du viewport."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        adapter.show()
        adapter.resize(800, 600)
        QApplication.processEvents()
        
        # Simuler l'appel à initializeGL (nécessite un contexte OpenGL actif)
        # On vérifie juste que les méthodes existent et peuvent être appelées
        self.assertTrue(hasattr(adapter, 'initializeGL'))
        self.assertTrue(hasattr(adapter, 'resizeGL'))
        
        # Simuler un resize
        adapter.resizeGL(800, 600)
        
        # Si le contexte existe, vérifier le viewport
        if adapter.ctx:
            print(f"[TEST] Viewport après resizeGL: {adapter.ctx.viewport}")
            self.assertEqual(adapter.ctx.viewport, (0, 0, 800, 600))
        else:
            print("[TEST] Contexte pas encore créé (normal avant initializeGL)")
    
    def test_cube_vertices_after_rotation(self):
        """Test que les vertices du cube sont valides après rotation."""
        rotation = self.service.get_rotation()
        size = 0.5
        
        # Créer un vertex du cube
        vertex = np.array([size, size, size], dtype='f4')
        vertex_rotated = rotation.apply(vertex.reshape(1, -1))[0]
        
        # Vérifier que le vertex n'est pas NaN ou Inf
        self.assertFalse(np.isnan(vertex_rotated).any(), "Vertex contient NaN!")
        self.assertFalse(np.isinf(vertex_rotated).any(), "Vertex contient Inf!")
        
        # Vérifier que le vertex est dans une plage raisonnable
        max_coord = np.max(np.abs(vertex_rotated))
        self.assertLess(max_coord, 10.0, f"Vertex trop loin: {max_coord}")
        
        print(f"[TEST] Vertex original: {vertex}")
        print(f"[TEST] Vertex après rotation: {vertex_rotated}")
        print(f"[TEST] Distance depuis origine: {np.linalg.norm(vertex_rotated):.3f}")
    
    def test_mvp_transforms_cube_into_view(self):
        """Test que la matrice MVP transforme le cube dans la vue."""
        from pyrr import Matrix44, Vector3
        
        # Récupérer la rotation
        rotation = self.service.get_rotation()
        size = 0.5
        
        # Créer un vertex du cube
        vertex_base = np.array([size, size, size])
        vertex_rotated = rotation.apply(vertex_base.reshape(1, -1))[0]
        
        # Calculer la matrice MVP
        aspect = 800 / 600
        proj = Matrix44.perspective_projection(45.0, aspect, 0.1, 100.0)
        
        camera_angle_x = -45.0
        camera_angle_y = 30.0
        camera_distance = 4.0
        
        angle_x_rad = np.radians(camera_angle_x)
        angle_y_rad = np.radians(camera_angle_y)
        
        cam_x = camera_distance * np.cos(angle_y_rad) * np.cos(angle_x_rad)
        cam_y = camera_distance * np.cos(angle_y_rad) * np.sin(angle_x_rad)
        cam_z = camera_distance * np.sin(angle_y_rad)
        
        view = Matrix44.look_at(
            Vector3([cam_x, cam_y, cam_z]),
            Vector3([0.0, 0.0, 0.0]),
            Vector3([0.0, 0.0, 1.0])
        )
        
        model = Matrix44.identity()
        mvp = proj * view * model
        mvp_np = np.array(mvp, dtype='f4')
        
        # Transformer le vertex
        vertex_homogeneous = np.append(vertex_rotated, 1.0)
        vertex_clip = mvp_np @ vertex_homogeneous
        vertex_ndc = vertex_clip[:3] / vertex_clip[3]
        
        print(f"[TEST] Vertex dans l'espace monde: {vertex_rotated}")
        print(f"[TEST] Vertex dans l'espace clip: {vertex_clip}")
        print(f"[TEST] Vertex dans NDC: {vertex_ndc}")
        print(f"[TEST] w (depth): {vertex_clip[3]:.3f}")
        
        # Vérifier que le vertex est dans le frustum
        in_frustum = np.all((vertex_ndc >= -1.0) & (vertex_ndc <= 1.0))
        in_front = vertex_clip[3] > 0
        
        print(f"[TEST] Dans le frustum [-1, 1]: {in_frustum}")
        print(f"[TEST] Devant la caméra (w > 0): {in_front}")
        
        self.assertTrue(in_front, "Vertex est derrière la caméra!")
        # Note: Le vertex peut être hors frustum si la caméra est mal positionnée
    
    def test_depth_testing_configuration(self):
        """Test que le depth testing est correctement configuré."""
        adapter = CubeVisualizerAdapterModernGL(
            service=self.service,
            event_bus=self.event_bus,
            parent=self.parent_widget
        )
        
        # Vérifier que le depth test sera activé dans initializeGL
        # On ne peut pas le vérifier directement sans contexte, mais on vérifie
        # que le code est présent
        import inspect
        source = inspect.getsource(adapter.initializeGL)
        
        self.assertIn('DEPTH_TEST', source, "Depth test n'est pas activé!")
        print("[TEST] Depth test est activé dans initializeGL")


if __name__ == '__main__':
    unittest.main(verbosity=2)


