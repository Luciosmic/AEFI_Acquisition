"""
Tests unitaires pour isoler le problème d'affichage du cube ModernGL.

Tests pour vérifier :
- Création du contexte OpenGL
- Création des VAOs (grille, cube, axes)
- Calcul de la matrice MVP
- Position de la caméra
- Vertices du cube
"""
import unittest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus
from infrastructure.messaging.command_bus import CommandBus
from domain.services.geometry_service import create_rotation_from_euler_xyz
from pyrr import Matrix44, Vector3


class TestModernGLAdapter(unittest.TestCase):
    """Tests pour isoler le problème d'affichage."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Créer les dépendances pour chaque test."""
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.service = CubeVisualizerService(
            command_bus=self.command_bus,
            event_bus=self.event_bus
        )
        # Note: On ne peut pas créer un vrai QOpenGLWidget sans contexte OpenGL
        # On va tester les méthodes individuelles
    
    def test_service_get_rotation(self):
        """Test que le service retourne une rotation valide."""
        rotation = self.service.get_rotation()
        self.assertIsNotNone(rotation)
        # Vérifier que c'est une Rotation de scipy
        self.assertTrue(hasattr(rotation, 'apply'))
        self.assertTrue(hasattr(rotation, 'as_matrix'))
        
        # Vérifier que la matrice est 3x3
        matrix = rotation.as_matrix()
        self.assertEqual(matrix.shape, (3, 3))
        print(f"[TEST] Rotation matrix shape: {matrix.shape}")
        print(f"[TEST] Rotation matrix:\n{matrix}")
    
    def test_cube_vertices_creation(self):
        """Test la création des vertices du cube."""
        rotation = self.service.get_rotation()
        size = 0.5
        
        vertices_base = np.array([
            [size, -size, -size], [size, size, -size], [size, size, size],
            [size, -size, -size], [size, size, size], [size, -size, size],
        ], dtype='f4')
        
        # Appliquer la rotation
        vertices_rotated = rotation.apply(vertices_base)
        
        self.assertEqual(vertices_rotated.shape[1], 3)  # 3D
        self.assertGreater(len(vertices_rotated), 0)
        
        # Vérifier que les vertices ne sont pas tous à (0,0,0)
        distances = np.linalg.norm(vertices_rotated, axis=1)
        max_distance = np.max(distances)
        self.assertGreater(max_distance, 0.1, "Les vertices sont trop proches de l'origine")
        
        print(f"[TEST] Vertices shape: {vertices_rotated.shape}")
        print(f"[TEST] Vertices range: min={np.min(vertices_rotated)}, max={np.max(vertices_rotated)}")
        print(f"[TEST] Max distance from origin: {max_distance}")
        print(f"[TEST] Sample vertices:\n{vertices_rotated[:3]}")
    
    def test_mvp_matrix_calculation(self):
        """Test le calcul de la matrice MVP."""
        # Créer un adapter mock pour tester _get_mvp_matrix
        adapter = MagicMock(spec=CubeVisualizerAdapterModernGL)
        adapter.width = MagicMock(return_value=800)
        adapter.height = MagicMock(return_value=600)
        adapter.camera_angle_x = -45.0
        adapter.camera_angle_y = 30.0
        adapter.camera_distance = 4.0
        
        # Calculer la matrice MVP comme dans le code
        aspect = 800 / 600
        proj = Matrix44.perspective_projection(45.0, aspect, 0.1, 100.0)
        
        angle_x_rad = np.radians(adapter.camera_angle_x)
        angle_y_rad = np.radians(adapter.camera_angle_y)
        
        cam_x = adapter.camera_distance * np.cos(angle_y_rad) * np.cos(angle_x_rad)
        cam_y = adapter.camera_distance * np.cos(angle_y_rad) * np.sin(angle_x_rad)
        cam_z = adapter.camera_distance * np.sin(angle_y_rad)
        
        view = Matrix44.look_at(
            Vector3([cam_x, cam_y, cam_z]),
            Vector3([0.0, 0.0, 0.0]),
            Vector3([0.0, 0.0, 1.0])
        )
        
        model = Matrix44.identity()
        mvp = proj * view * model
        mvp = np.array(mvp, dtype='f4')
        
        self.assertIsNotNone(mvp)
        self.assertEqual(mvp.shape, (4, 4))
        self.assertEqual(mvp.dtype, np.dtype('f4'))
        
        print(f"[TEST] MVP matrix shape: {mvp.shape}")
        print(f"[TEST] MVP matrix:\n{mvp}")
        
        # Vérifier que la matrice n'est pas identité (sinon rien ne serait transformé)
        identity = np.eye(4, dtype='f4')
        self.assertFalse(np.allclose(mvp, identity), "La matrice MVP est identité!")
    
    def test_camera_position(self):
        """Test la position de la caméra."""
        adapter = MagicMock(spec=CubeVisualizerAdapterModernGL)
        adapter.camera_angle_x = -45.0
        adapter.camera_angle_y = 30.0
        adapter.camera_distance = 4.0
        
        # Calculer la position de la caméra comme dans le code
        angle_x_rad = np.radians(adapter.camera_angle_x)
        angle_y_rad = np.radians(adapter.camera_angle_y)
        
        cam_x = adapter.camera_distance * np.cos(angle_y_rad) * np.cos(angle_x_rad)
        cam_y = adapter.camera_distance * np.cos(angle_y_rad) * np.sin(angle_x_rad)
        cam_z = adapter.camera_distance * np.sin(angle_y_rad)
        
        cam_pos = np.array([cam_x, cam_y, cam_z])
        distance = np.linalg.norm(cam_pos)
        
        self.assertAlmostEqual(distance, adapter.camera_distance, places=1)
        print(f"[TEST] Camera position: ({cam_x:.2f}, {cam_y:.2f}, {cam_z:.2f})")
        print(f"[TEST] Camera distance from origin: {distance:.2f}")
        
        # Vérifier que la caméra n'est pas à l'origine
        self.assertGreater(distance, 0.1, "La caméra est trop proche de l'origine")
    
    def test_cube_bounds(self):
        """Test que le cube est dans les limites visibles."""
        rotation = self.service.get_rotation()
        size = 0.5
        
        # Créer tous les vertices du cube
        vertices_base = np.array([
            [size, -size, -size], [size, size, -size], [size, size, size],
            [size, -size, -size], [size, size, size], [size, -size, size],
            [-size, size, -size], [-size, -size, -size], [-size, -size, size],
            [-size, size, -size], [-size, -size, size], [-size, size, size],
            [-size, size, -size], [size, size, -size], [size, size, size],
            [-size, size, -size], [size, size, size], [-size, size, size],
            [size, -size, -size], [-size, -size, -size], [-size, -size, size],
            [size, -size, -size], [-size, -size, size], [size, -size, size],
            [-size, -size, size], [size, -size, size], [size, size, size],
            [-size, -size, size], [size, size, size], [-size, size, size],
            [size, -size, -size], [-size, -size, -size], [-size, size, -size],
            [size, -size, -size], [-size, size, -size], [size, size, -size],
        ], dtype='f4')
        
        vertices_rotated = rotation.apply(vertices_base)
        
        # Calculer les bounds
        min_bounds = np.min(vertices_rotated, axis=0)
        max_bounds = np.max(vertices_rotated, axis=0)
        center = (min_bounds + max_bounds) / 2
        
        print(f"[TEST] Cube bounds:")
        print(f"  Min: ({min_bounds[0]:.2f}, {min_bounds[1]:.2f}, {min_bounds[2]:.2f})")
        print(f"  Max: ({max_bounds[0]:.2f}, {max_bounds[1]:.2f}, {max_bounds[2]:.2f})")
        print(f"  Center: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
        print(f"  Size: ({max_bounds[0]-min_bounds[0]:.2f}, {max_bounds[1]-min_bounds[1]:.2f}, {max_bounds[2]-min_bounds[2]:.2f})")
        
        # Vérifier que le cube n'est pas à l'origine (après rotation)
        distance_from_origin = np.linalg.norm(center)
        print(f"  Distance from origin: {distance_from_origin:.2f}")
        
        # Le cube devrait être centré près de l'origine (mais peut être décalé après rotation)
        self.assertLess(distance_from_origin, 2.0, "Le cube est trop loin de l'origine")
    
    def test_viewport_size(self):
        """Test que le viewport a une taille valide."""
        # Simuler un widget avec des dimensions
        width = 800
        height = 600
        
        self.assertGreater(width, 0, "Largeur du viewport invalide")
        self.assertGreater(height, 0, "Hauteur du viewport invalide")
        
        aspect = width / height
        print(f"[TEST] Viewport: {width}x{height}, aspect={aspect:.2f}")
        
        # L'aspect ratio devrait être raisonnable
        self.assertGreater(aspect, 0.1)
        self.assertLess(aspect, 10.0)
    
    def test_colors_not_white(self):
        """Test que les couleurs du cube ne sont pas blanches (invisibles sur fond blanc)."""
        color_x = CubeVisualizerAdapterModernGL.COLOR_X
        color_y = CubeVisualizerAdapterModernGL.COLOR_Y
        color_z = CubeVisualizerAdapterModernGL.COLOR_Z
        
        # Vérifier que les couleurs ne sont pas blanches (1.0, 1.0, 1.0)
        white = np.array([1.0, 1.0, 1.0])
        
        self.assertFalse(np.allclose(color_x, white), f"COLOR_X est blanc: {color_x}")
        self.assertFalse(np.allclose(color_y, white), f"COLOR_Y est blanc: {color_y}")
        self.assertFalse(np.allclose(color_z, white), f"COLOR_Z est blanc: {color_z}")
        
        print(f"[TEST] Colors:")
        print(f"  X (blue): {color_x}")
        print(f"  Y (yellow): {color_y}")
        print(f"  Z (red): {color_z}")
    
    def test_cube_visibility_after_mvp(self):
        """Test que le cube est visible après transformation MVP."""
        # Créer les vertices du cube
        rotation = self.service.get_rotation()
        size = 0.5
        vertices_base = np.array([
            [size, -size, -size], [size, size, -size], [size, size, size],
            [size, -size, -size], [size, size, size], [size, -size, size],
            [-size, size, -size], [-size, -size, -size], [-size, -size, size],
            [-size, size, -size], [-size, -size, size], [-size, size, size],
            [-size, size, -size], [size, size, -size], [size, size, size],
            [-size, size, -size], [size, size, size], [-size, size, size],
            [size, -size, -size], [-size, -size, -size], [-size, -size, size],
            [size, -size, -size], [-size, -size, size], [size, -size, size],
            [-size, -size, size], [size, -size, size], [size, size, size],
            [-size, -size, size], [size, size, size], [-size, size, size],
            [size, -size, -size], [-size, -size, -size], [-size, size, -size],
            [size, -size, -size], [-size, size, -size], [size, size, -size],
        ], dtype='f4')
        
        vertices_rotated = rotation.apply(vertices_base)
        
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
        
        # Transformer les vertices
        vertices_homogeneous = np.column_stack([vertices_rotated, np.ones(len(vertices_rotated))])
        vertices_clip = (mvp_np @ vertices_homogeneous.T).T
        
        # Normaliser par w (perspective divide)
        vertices_ndc = vertices_clip[:, :3] / vertices_clip[:, 3:4]
        
        # Vérifier que les vertices sont dans le frustum NDC [-1, 1]
        in_frustum = np.all(
            (vertices_ndc >= -1.0) & (vertices_ndc <= 1.0),
            axis=1
        )
        
        vertices_in_frustum = np.sum(in_frustum)
        total_vertices = len(vertices_ndc)
        
        print(f"[TEST] Vertices visibility after MVP:")
        print(f"  Total vertices: {total_vertices}")
        print(f"  Vertices in frustum [-1, 1]: {vertices_in_frustum} ({100*vertices_in_frustum/total_vertices:.1f}%)")
        print(f"  NDC bounds: min={np.min(vertices_ndc, axis=0)}, max={np.max(vertices_ndc, axis=0)}")
        print(f"  Sample NDC vertices:\n{vertices_ndc[:3]}")
        
        # Au moins quelques vertices devraient être visibles
        self.assertGreater(vertices_in_frustum, 0, "Aucun vertex n'est dans le frustum de vue!")
        
        # Vérifier que les valeurs w sont positives (sinon le vertex est derrière la caméra)
        w_values = vertices_clip[:, 3]
        positive_w = np.sum(w_values > 0)
        print(f"  Vertices with positive w (in front of camera): {positive_w}/{total_vertices}")
        self.assertGreater(positive_w, 0, "Aucun vertex n'est devant la caméra!")


if __name__ == '__main__':
    unittest.main(verbosity=2)

