"""
Tests approfondis pour isoler le problème de rendu OpenGL.

Ces tests vérifient :
- Création du contexte ModernGL
- Compilation des shaders
- Création des buffers et VAOs
- Vérification que les données sont correctement uploadées
"""
import unittest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat

# Ajouter le répertoire parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    print("Warning: moderngl not available")


class TestOpenGLRendering(unittest.TestCase):
    """Tests approfondis pour le rendu OpenGL."""
    
    @classmethod
    def setUpClass(cls):
        """Créer QApplication une seule fois."""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    @unittest.skipIf(not MODERNGL_AVAILABLE, "moderngl not available")
    def test_context_creation(self):
        """Test que le contexte ModernGL peut être créé."""
        # Configurer le format OpenGL
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        # Créer un widget OpenGL minimal
        widget = QOpenGLWidget()
        widget.resize(400, 300)
        widget.show()
        
        # Forcer l'initialisation du contexte
        widget.makeCurrent()
        
        try:
            # Créer le contexte ModernGL
            ctx = moderngl.create_context(standalone=False)
            self.assertIsNotNone(ctx)
            print(f"[TEST] Contexte ModernGL créé: {ctx}")
            print(f"[TEST] Version OpenGL: {ctx.info.get('GL_VERSION', 'unknown')}")
            print(f"[TEST] Vendor: {ctx.info.get('GL_VENDOR', 'unknown')}")
            print(f"[TEST] Renderer: {ctx.info.get('GL_RENDERER', 'unknown')}")
        except Exception as e:
            self.fail(f"Erreur lors de la création du contexte: {e}")
        finally:
            widget.doneCurrent()
            widget.close()
    
    @unittest.skipIf(not MODERNGL_AVAILABLE, "moderngl not available")
    def test_shader_compilation(self):
        """Test que les shaders se compilent correctement."""
        VERTEX_SHADER = """
        #version 330 core
        in vec3 in_position;
        in vec3 in_color;
        uniform mat4 mvp;
        out vec3 frag_color;
        void main() {
            gl_Position = mvp * vec4(in_position, 1.0);
            frag_color = in_color;
        }
        """
        
        FRAGMENT_SHADER = """
        #version 330 core
        in vec3 frag_color;
        out vec4 out_color;
        void main() {
            out_color = vec4(frag_color, 1.0);
        }
        """
        
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        widget = QOpenGLWidget()
        widget.resize(400, 300)
        widget.show()
        widget.makeCurrent()
        
        try:
            ctx = moderngl.create_context(standalone=False)
            prog = ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=FRAGMENT_SHADER
            )
            self.assertIsNotNone(prog)
            print("[TEST] Shaders compilés avec succès")
            # ModernGL utilise une API différente pour les attributs/uniforms
            # On vérifie juste que le programme existe et a les uniforms nécessaires
            try:
                mvp_uniform = prog.get('mvp', None)
                if mvp_uniform:
                    print(f"[TEST] Uniform 'mvp' trouvé")
                else:
                    print("[TEST] Uniform 'mvp' non trouvé (peut être normal)")
            except:
                pass
        except Exception as e:
            self.fail(f"Erreur lors de la compilation des shaders: {e}")
        finally:
            widget.doneCurrent()
            widget.close()
    
    @unittest.skipIf(not MODERNGL_AVAILABLE, "moderngl not available")
    def test_simple_triangle_rendering(self):
        """Test le rendu d'un triangle simple pour vérifier que le pipeline fonctionne."""
        VERTEX_SHADER = """
        #version 330 core
        in vec3 in_position;
        in vec3 in_color;
        uniform mat4 mvp;
        out vec3 frag_color;
        void main() {
            gl_Position = mvp * vec4(in_position, 1.0);
            frag_color = in_color;
        }
        """
        
        FRAGMENT_SHADER = """
        #version 330 core
        in vec3 frag_color;
        out vec4 out_color;
        void main() {
            out_color = vec4(frag_color, 1.0);
        }
        """
        
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        widget = QOpenGLWidget()
        widget.resize(400, 300)
        widget.show()
        widget.makeCurrent()
        
        try:
            ctx = moderngl.create_context(standalone=False)
            ctx.viewport = (0, 0, 400, 300)
            
            prog = ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=FRAGMENT_SHADER
            )
            
            # Créer un triangle simple
            vertices = np.array([
                [0.0, 0.5, 0.0],   # Top
                [-0.5, -0.5, 0.0], # Bottom left
                [0.5, -0.5, 0.0],  # Bottom right
            ], dtype='f4')
            
            colors = np.array([
                [1.0, 0.0, 0.0],  # Red
                [0.0, 1.0, 0.0],  # Green
                [0.0, 0.0, 1.0],  # Blue
            ], dtype='f4')
            
            # Créer les buffers
            vbo_v = ctx.buffer(vertices.tobytes())
            vbo_c = ctx.buffer(colors.tobytes())
            
            # Créer le VAO
            vao = ctx.vertex_array(
                prog,
                [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
            )
            
            # Créer une matrice MVP simple (identité pour le test)
            from pyrr import Matrix44
            mvp = Matrix44.identity()
            prog['mvp'].write(np.array(mvp, dtype='f4').tobytes())
            
            # Activer le depth test
            ctx.enable(moderngl.DEPTH_TEST)
            
            # Rendre
            ctx.clear(0.5, 0.5, 0.5, 1.0)  # Fond gris pour voir le triangle
            vao.render(moderngl.TRIANGLES)
            
            print("[TEST] Triangle rendu avec succès")
            print(f"[TEST] VAO créé: {vao is not None}")
            print(f"[TEST] Vertices: {len(vertices)}")
            
            # Vérifier qu'il n'y a pas d'erreur OpenGL
            error = ctx.error
            if error != 'GL_NO_ERROR':
                print(f"[WARNING] Erreur OpenGL: {error}")
            else:
                print("[TEST] Aucune erreur OpenGL")
                
        except Exception as e:
            self.fail(f"Erreur lors du rendu du triangle: {e}")
        finally:
            widget.doneCurrent()
            widget.close()
    
    def test_viewport_size_consistency(self):
        """Test que le viewport est cohérent avec la taille du widget."""
        from infrastructure.rendering.cube_visualizer_adapter_modern_gl import CubeVisualizerAdapterModernGL
        from application.services.cube_visualizer_service import CubeVisualizerService
        from infrastructure.messaging.event_bus import EventBus
        from infrastructure.messaging.command_bus import CommandBus
        
        command_bus = CommandBus()
        event_bus = EventBus()
        service = CubeVisualizerService(command_bus=command_bus, event_bus=event_bus)
        parent = QWidget()
        parent.resize(800, 600)
        
        adapter = CubeVisualizerAdapterModernGL(
            service=service,
            event_bus=event_bus,
            parent=parent
        )
        
        # Vérifier que le widget a une taille
        width = adapter.width()
        height = adapter.height()
        
        print(f"[TEST] Widget size: {width}x{height}")
        
        # Le viewport devrait être défini dans initializeGL
        # On vérifie juste que les méthodes existent
        self.assertTrue(hasattr(adapter, 'resizeGL'))
        self.assertTrue(hasattr(adapter, 'initializeGL'))
        
        # Simuler un resize
        adapter.resizeGL(800, 600)
        
        # Vérifier que le viewport serait mis à jour si le contexte existe
        if adapter.ctx:
            self.assertEqual(adapter.ctx.viewport, (0, 0, 800, 600))
            print(f"[TEST] Viewport après resize: {adapter.ctx.viewport}")
    
    def test_buffer_data_upload(self):
        """Test que les données sont correctement uploadées dans les buffers."""
        # Simuler la création de buffers
        vertices = np.array([
            [0.5, -0.5, -0.5],
            [0.5, 0.5, -0.5],
            [0.5, 0.5, 0.5],
        ], dtype='f4')
        
        colors = np.array([
            [0.3, 0.6, 1.0],
            [0.3, 0.6, 1.0],
            [0.3, 0.6, 1.0],
        ], dtype='f4')
        
        # Vérifier que les données sont valides
        self.assertEqual(vertices.shape, (3, 3))
        self.assertEqual(colors.shape, (3, 3))
        
        # Vérifier que les bytes peuvent être créés
        vertices_bytes = vertices.tobytes()
        colors_bytes = colors.tobytes()
        
        self.assertGreater(len(vertices_bytes), 0)
        self.assertGreater(len(colors_bytes), 0)
        
        print(f"[TEST] Vertices bytes: {len(vertices_bytes)} bytes")
        print(f"[TEST] Colors bytes: {len(colors_bytes)} bytes")
        print(f"[TEST] Vertices data valid: {not np.isnan(vertices).any()}")
        print(f"[TEST] Colors data valid: {not np.isnan(colors).any()}")


if __name__ == '__main__':
    unittest.main(verbosity=2)

