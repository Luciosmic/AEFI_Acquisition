"""
Adapter ModernGL pour la visualisation du cube sensor intégré dans Qt.

Utilise QOpenGLWidget pour intégrer ModernGL directement dans l'UI Qt.
"""
import moderngl
import numpy as np
from scipy.spatial.transform import Rotation as R
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QSurfaceFormat
from typing import Optional
from application.services.cube_visualizer_service import CubeVisualizerService
from infrastructure.messaging.event_bus import EventBus, Event, EventType

# Shaders GLSL
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


class CubeVisualizerAdapterModernGL(QOpenGLWidget):
    """
    Adapter ModernGL intégré dans Qt via QOpenGLWidget.
    
    Responsabilités:
    - Rendu OpenGL du cube avec rotation
    - Intégration dans l'UI Qt
    - Synchronisation avec le service via EventBus
    """
    
    # Couleurs des axes (RGB [0-1])
    COLOR_X = [0.3, 0.6, 1.0]  # Bleu
    COLOR_Y = [1.0, 0.9, 0.2]  # Jaune
    COLOR_Z = [1.0, 0.2, 0.2]  # Rouge
    
    def __init__(
        self,
        service: CubeVisualizerService,
        event_bus: EventBus,
        parent=None
    ):
        """
        Args:
            service: Service de visualisation (pour queries)
            event_bus: EventBus pour recevoir les événements
            parent: Widget parent Qt
        """
        # Configurer le format OpenGL avant d'appeler super().__init__()
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__(parent)
        self.service = service
        self.event_bus = event_bus
        
        # Contexte ModernGL (sera créé dans initializeGL)
        self.ctx: Optional[moderngl.Context] = None
        self.prog: Optional[moderngl.Program] = None
        
        # VAOs pour le rendu
        self.cube_vao = None
        self.grid_vao = None
        self.axes_vaos = []
        
        # État de la caméra
        self.camera_distance = 4.0
        self.camera_angle_x = -45.0  # Azimuth
        self.camera_angle_y = 30.0   # Elevation
        
        # S'abonner aux événements
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_event)
        self.event_bus.subscribe(EventType.CAMERA_VIEW_CHANGED, self._on_camera_view_changed_event)
        
        # Timer pour le rendu continu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        self._paint_count = 0  # Compteur pour debug
    
    def initializeGL(self):
        """Initialise le contexte OpenGL et les ressources."""
        print("[DEBUG] initializeGL() appelé")
        try:
            # Créer le contexte ModernGL depuis le contexte Qt
            # QOpenGLWidget fournit déjà un contexte OpenGL actif
            self.ctx = moderngl.create_context(standalone=False)
            print(f"[DEBUG] Contexte ModernGL créé: {self.ctx}")
            
            # Définir le viewport
            width = self.width()
            height = self.height()
            if width == 0:
                width = 400  # Valeur par défaut
            if height == 0:
                height = 400  # Valeur par défaut
            self.ctx.viewport = (0, 0, width, height)
            print(f"[DEBUG] Viewport défini: {width}x{height}")
            
            # Créer le programme shader
            self.prog = self.ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=FRAGMENT_SHADER
            )
            print("[DEBUG] Programme shader créé")
            
            # Activer le depth testing
            self.ctx.enable(moderngl.DEPTH_TEST)
            print("[DEBUG] Depth test activé")
            
            # Créer les géométries
            print("[DEBUG] Création de la grille...")
            self._create_grid()
            print(f"[DEBUG] Grille créée: {self.grid_vao is not None}")
            
            print("[DEBUG] Création du cube...")
            self._create_cube()
            print(f"[DEBUG] Cube créé: {self.cube_vao is not None}")
            
            print("[DEBUG] Création des axes...")
            self._create_axes()
            print(f"[DEBUG] Axes créés: {len(self.axes_vaos)} VAOs")
            
            print("[DEBUG] initializeGL() terminé")
        except Exception as e:
            print(f"[ERROR] Erreur dans initializeGL: {e}")
            import traceback
            traceback.print_exc()
    
    def resizeGL(self, width: int, height: int):
        """Appelé quand le widget est redimensionné."""
        if self.ctx:
            self.ctx.viewport = (0, 0, width, height)
    
    def paintGL(self):
        """Appelé pour le rendu de la frame."""
        if not self.ctx or not self.prog:
            return
        
        try:
            self._paint_count += 1
            if self._paint_count <= 3:  # Log seulement les 3 premières frames
                print(f"[DEBUG] paintGL appelé (frame {self._paint_count})")
            
            # S'assurer que le viewport est à jour
            width = self.width()
            height = self.height()
            if width > 0 and height > 0:
                self.ctx.viewport = (0, 0, width, height)
                if self._paint_count <= 3:
                    print(f"[DEBUG] Viewport dans paintGL: {self.ctx.viewport}, widget size: {width}x{height}")
            else:
                if self._paint_count <= 3:
                    print(f"[WARNING] Widget size invalide dans paintGL: {width}x{height}")
            
            # Effacer le buffer avec une couleur visible pour debug (gris clair au lieu de blanc)
            # Si on voit du gris, le widget rend mais le cube n'est pas visible
            self.ctx.clear(0.9, 0.9, 0.9, 1.0)  # Fond gris clair pour debug
            
            # Calculer la matrice MVP
            mvp = self._get_mvp_matrix()
            self.prog['mvp'].write(mvp.astype('f4').tobytes())
            
            # Rendre la grille (statique)
            if self.grid_vao:
                self.grid_vao.render(moderngl.LINES)
                if self._paint_count <= 3:
                    print(f"[DEBUG] Grille rendue")
            
            # Rendre le cube (roté)
            if self.cube_vao:
                self.cube_vao.render(moderngl.TRIANGLES)
                if self._paint_count <= 3:
                    print(f"[DEBUG] Cube rendu")
            else:
                if self._paint_count <= 3:
                    print("[DEBUG] paintGL: cube_vao est None!")
            
            # Rendre les axes
            for vao, _ in self.axes_vaos:
                vao.render(moderngl.LINES)
            if self._paint_count <= 3:
                print(f"[DEBUG] {len(self.axes_vaos)} axes rendus")
                
        except Exception as e:
            print(f"[ERROR] Erreur dans paintGL: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_angles_changed_event(self, event: Event):
        """Handler pour l'événement ANGLES_CHANGED."""
        print(f"[DEBUG] _on_angles_changed_event: {event.data}")
        # Mettre à jour le cube et les axes avec la nouvelle rotation
        self._create_cube()
        self._create_axes()
        self.update()  # Déclencher un redraw
    
    def _on_camera_view_changed_event(self, event: Event):
        """Handler pour l'événement CAMERA_VIEW_CHANGED."""
        view_name = event.data.get('view_name', '3d')
        self._reset_camera_view(view_name)
        self.update()
    
    def _reset_camera_view(self, view_name: str):
        """Remet la caméra à sa position par défaut pour une vue."""
        camera_positions = {
            '3d': {'angle_x': -45.0, 'angle_y': 30.0, 'distance': 4.0},
            'xy': {'angle_x': 0.0, 'angle_y': 90.0, 'distance': 3.0},
            'xz': {'angle_x': 0.0, 'angle_y': 0.0, 'distance': 3.0},
            'yz': {'angle_x': 90.0, 'angle_y': 0.0, 'distance': 3.0},
        }
        if view_name in camera_positions:
            pos = camera_positions[view_name]
            self.camera_angle_x = pos['angle_x']
            self.camera_angle_y = pos['angle_y']
            self.camera_distance = pos['distance']
    
    def _get_mvp_matrix(self) -> np.ndarray:
        """Calcule la matrice Model-View-Projection."""
        from pyrr import Matrix44, Vector3
        
        # Projection
        aspect = self.width() / self.height() if self.height() > 0 else 1.0
        proj = Matrix44.perspective_projection(45.0, aspect, 0.1, 100.0)
        
        # View (caméra)
        # Convertir les angles en position de caméra
        angle_x_rad = np.radians(self.camera_angle_x)
        angle_y_rad = np.radians(self.camera_angle_y)
        
        cam_x = self.camera_distance * np.cos(angle_y_rad) * np.cos(angle_x_rad)
        cam_y = self.camera_distance * np.cos(angle_y_rad) * np.sin(angle_x_rad)
        cam_z = self.camera_distance * np.sin(angle_y_rad)
        
        view = Matrix44.look_at(
            Vector3([cam_x, cam_y, cam_z]),
            Vector3([0.0, 0.0, 0.0]),
            Vector3([0.0, 0.0, 1.0])
        )
        
        # Model (identité pour le cube, la rotation est dans les vertices)
        model = Matrix44.identity()
        
        # MVP = Projection * View * Model
        mvp = proj * view * model
        return np.array(mvp, dtype='f4')
    
    def _create_grid(self):
        """Crée la grille statique (non-rotée)."""
        if not self.ctx or not self.prog:
            print("[ERROR] _create_grid: ctx ou prog manquant")
            return
        
        grid_size = 5
        grid_lines = []
        
        for i in range(-grid_size, grid_size + 1):
            # Lignes X
            grid_lines.extend([[i, -grid_size, 0], [i, grid_size, 0]])
            # Lignes Y
            grid_lines.extend([[-grid_size, i, 0], [grid_size, i, 0]])
        
        vertices = np.array(grid_lines, dtype='f4')
        colors = np.array([[0.8, 0.8, 0.8]] * len(vertices), dtype='f4')
        
        vbo_v = self.ctx.buffer(vertices.tobytes())
        vbo_c = self.ctx.buffer(colors.tobytes())
        
        self.grid_vao = self.ctx.vertex_array(
            self.prog,
            [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
        )
        print(f"[DEBUG] Grille créée: {len(vertices)} vertices")
    
    def _create_cube(self):
        """Crée le cube avec rotation appliquée."""
        if not self.ctx or not self.prog:
            print("[ERROR] _create_cube: ctx ou prog manquant")
            return
        
        try:
            # Récupérer la rotation depuis le service
            rotation = self.service.get_rotation()
            print(f"[DEBUG] Rotation récupérée: {rotation}")
            
            # Créer les vertices du cube (centré à l'origine, taille 1.0)
            size = 0.5
            vertices_base = np.array([
                # Face +X (bleu)
                [size, -size, -size], [size, size, -size], [size, size, size],
                [size, -size, -size], [size, size, size], [size, -size, size],
                # Face -X (bleu)
                [-size, size, -size], [-size, -size, -size], [-size, -size, size],
                [-size, size, -size], [-size, -size, size], [-size, size, size],
                # Face +Y (jaune)
                [-size, size, -size], [size, size, -size], [size, size, size],
                [-size, size, -size], [size, size, size], [-size, size, size],
                # Face -Y (jaune)
                [size, -size, -size], [-size, -size, -size], [-size, -size, size],
                [size, -size, -size], [-size, -size, size], [size, -size, size],
                # Face +Z (rouge)
                [-size, -size, size], [size, -size, size], [size, size, size],
                [-size, -size, size], [size, size, size], [-size, size, size],
                # Face -Z (rouge)
                [size, -size, -size], [-size, -size, -size], [-size, size, -size],
                [size, -size, -size], [-size, size, -size], [size, size, -size],
            ], dtype='f4')
            
            # Appliquer la rotation
            vertices_rotated = rotation.apply(vertices_base)
            
            # Couleurs pour chaque face
            colors = np.array([
                self.COLOR_X * 6,  # +X
                self.COLOR_X * 6,  # -X
                self.COLOR_Y * 6,  # +Y
                self.COLOR_Y * 6,  # -Y
                self.COLOR_Z * 6,  # +Z
                self.COLOR_Z * 6,  # -Z
            ], dtype='f4').flatten()
            
            vbo_v = self.ctx.buffer(vertices_rotated.astype('f4').tobytes())
            vbo_c = self.ctx.buffer(colors.tobytes())
            
            self.cube_vao = self.ctx.vertex_array(
                self.prog,
                [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
            )
            print(f"[DEBUG] Cube créé: {len(vertices_rotated)} vertices, VAO={self.cube_vao is not None}")
        except Exception as e:
            print(f"[ERROR] Erreur dans _create_cube: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_axes(self):
        """Crée les axes _mes (rotés) et _labo (fixes)."""
        if not self.ctx or not self.prog:
            return
        
        rotation = self.service.get_rotation()
        axis_length = 0.8
        
        # Axes _mes (rotés)
        axes_mes = [
            (np.array([0, 0, 0], dtype='f4'), np.array([axis_length, 0, 0], dtype='f4'), self.COLOR_X),
            (np.array([0, 0, 0], dtype='f4'), np.array([0, axis_length, 0], dtype='f4'), self.COLOR_Y),
            (np.array([0, 0, 0], dtype='f4'), np.array([0, 0, axis_length], dtype='f4'), self.COLOR_Z),
        ]
        
        # Axes _labo (fixes, plus longs)
        labo_length = 1.5
        axes_labo = [
            (np.array([0, 0, 0], dtype='f4'), np.array([labo_length, 0, 0], dtype='f4'), self.COLOR_X),
            (np.array([0, 0, 0], dtype='f4'), np.array([0, labo_length, 0], dtype='f4'), self.COLOR_Y),
            (np.array([0, 0, 0], dtype='f4'), np.array([0, 0, labo_length], dtype='f4'), self.COLOR_Z),
        ]
        
        self.axes_vaos = []
        
        # Créer les VAOs pour les axes _mes
        for start, end, color in axes_mes:
            start_rotated = rotation.apply(start.reshape(1, -1))[0]
            end_rotated = rotation.apply(end.reshape(1, -1))[0]
            
            vertices = np.array([start_rotated, end_rotated], dtype='f4')
            colors = np.array([color, color], dtype='f4')
            
            vbo_v = self.ctx.buffer(vertices.tobytes())
            vbo_c = self.ctx.buffer(colors.tobytes())
            
            vao = self.ctx.vertex_array(
                self.prog,
                [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
            )
            self.axes_vaos.append((vao, 'mes'))
        
        # Créer les VAOs pour les axes _labo (non-rotés)
        for start, end, color in axes_labo:
            vertices = np.array([start, end], dtype='f4')
            colors = np.array([color, color], dtype='f4')
            
            vbo_v = self.ctx.buffer(vertices.tobytes())
            vbo_c = self.ctx.buffer(colors.tobytes())
            
            vao = self.ctx.vertex_array(
                self.prog,
                [(vbo_v, '3f', 'in_position'), (vbo_c, '3f', 'in_color')]
            )
            self.axes_vaos.append((vao, 'labo'))
    
    def get_widget(self):
        """Retourne le widget Qt (soi-même)."""
        return self

