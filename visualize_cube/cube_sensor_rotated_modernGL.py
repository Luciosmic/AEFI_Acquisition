"""
Visualisation du cube sensor avec rotation physique et couleurs des axes - Version ModernGL.

Architecture MVP :
- View : Rendu OpenGL, gestion de la fenêtre, callbacks d'interaction
- Presenter : Logique métier (rotation du sensor, état de la caméra)
"""
import moderngl
import numpy as np
from scipy.spatial.transform import Rotation as R
import math
import glfw
from pyrr import Matrix44, Vector3
from dataclasses import dataclass
from typing import Optional

# Shaders GLSL
VERTEX_SHADER = """
#version 330 core

in vec3 in_position;
in vec3 in_color;

uniform mat4 mvp;
uniform mat4 model;

out vec3 frag_color;

void main() {
    gl_Position = mvp * model * vec4(in_position, 1.0);
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


@dataclass
class SensorOrientation:
    """Value Object représentant l'orientation du sensor."""
    theta_x_deg: float
    theta_y_deg: float
    theta_z_deg: float
    
    def to_rotation_matrix(self) -> Matrix44:
        """Convertit l'orientation en matrice de rotation."""
        rotation = R.from_euler('xyz', [self.theta_x_deg, self.theta_y_deg, self.theta_z_deg], degrees=True)
        # rotation.as_matrix() retourne une matrice 3x3, on la convertit en Matrix44
        mat33 = rotation.as_matrix()
        return Matrix44.from_matrix33(mat33)


@dataclass
class CameraState:
    """Value Object représentant l'état de la caméra."""
    distance: float = 4.0
    angle_x: float = -45.0  # Azimuth
    angle_y: float = 30.0   # Elevation
    target: Vector3 = None
    
    def __post_init__(self):
        if self.target is None:
            self.target = Vector3([0.0, 0.0, 0.0])


class CubeSensorView:
    """
    View : Gère le rendu OpenGL et les interactions utilisateur.
    Responsabilité : Affichage, callbacks d'événements, gestion des ressources OpenGL.
    """
    
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        
        # Initialiser GLFW
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # Requis pour macOS
        
        self.window = glfw.create_window(width, height, "Cube Sensor - ModernGL", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create window")
        
        glfw.make_context_current(self.window)
        glfw.set_window_size_callback(self.window, self._on_resize)
        
        # Créer le contexte ModernGL
        self.ctx = moderngl.create_context()
        
        # Créer le programme shader
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER
        )
        
        # Callbacks pour les événements (seront connectés par le presenter)
        self.on_mouse_button = None
        self.on_mouse_move = None
        self.on_scroll = None
        self.on_key = None
        
        # Variables pour l'interaction
        self.last_mouse_x = 0.0
        self.last_mouse_y = 0.0
        self.mouse_dragging = False
        
        # Activer le depth testing
        self.ctx.enable(moderngl.DEPTH_TEST)
        
        # Créer la grille statique
        self._create_grid()
    
    def _on_resize(self, window, width, height):
        self.width = width
        self.height = height
        self.ctx.viewport = (0, 0, width, height)
    
    def setup_callbacks(self, presenter):
        """Connecte les callbacks aux méthodes du presenter."""
        glfw.set_mouse_button_callback(self.window, self._create_mouse_button_callback(presenter))
        glfw.set_cursor_pos_callback(self.window, self._create_mouse_move_callback(presenter))
        glfw.set_scroll_callback(self.window, self._create_scroll_callback(presenter))
        glfw.set_key_callback(self.window, self._create_key_callback(presenter))
    
    def _create_mouse_button_callback(self, presenter):
        def callback(window, button, action, mods):
            if button == glfw.MOUSE_BUTTON_LEFT:
                if action == glfw.PRESS:
                    self.mouse_dragging = True
                    x, y = glfw.get_cursor_pos(window)
                    self.last_mouse_x = x
                    self.last_mouse_y = y
                elif action == glfw.RELEASE:
                    self.mouse_dragging = False
        return callback
    
    def _create_mouse_move_callback(self, presenter):
        def callback(window, x, y):
            if self.mouse_dragging:
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y
                presenter.on_camera_rotate(dx, dy)
                self.last_mouse_x = x
                self.last_mouse_y = y
        return callback
    
    def _create_scroll_callback(self, presenter):
        def callback(window, xoffset, yoffset):
            presenter.on_camera_zoom(yoffset)
        return callback
    
    def _create_key_callback(self, presenter):
        def callback(window, key, scancode, action, mods):
            if action == glfw.PRESS or action == glfw.REPEAT:
                presenter.on_key_press(key)
        return callback
    
    def create_cube_geometry(self, size=1.0):
        """Crée la géométrie du cube (vertices, colors, indices)."""
        s = size / 2.0
        
        vertices = np.array([
            # Face +X (bleu)
            [s, -s, -s], [s, s, -s], [s, s, s], [s, -s, s],
            # Face -X (bleu)
            [-s, s, -s], [-s, -s, -s], [-s, -s, s], [-s, s, s],
            # Face +Y (jaune)
            [-s, s, -s], [s, s, -s], [s, s, s], [-s, s, s],
            # Face -Y (jaune)
            [s, -s, -s], [-s, -s, -s], [-s, -s, s], [s, -s, s],
            # Face +Z (rouge)
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
            # Face -Z (rouge)
            [s, -s, -s], [-s, -s, -s], [-s, s, -s], [s, s, -s],
        ], dtype='f4')
        
        colors = np.array([
            # Face +X (bleu)
            [0.3, 0.6, 1.0], [0.3, 0.6, 1.0], [0.3, 0.6, 1.0], [0.3, 0.6, 1.0],
            # Face -X (bleu)
            [0.3, 0.6, 1.0], [0.3, 0.6, 1.0], [0.3, 0.6, 1.0], [0.3, 0.6, 1.0],
            # Face +Y (jaune)
            [1.0, 0.9, 0.2], [1.0, 0.9, 0.2], [1.0, 0.9, 0.2], [1.0, 0.9, 0.2],
            # Face -Y (jaune)
            [1.0, 0.9, 0.2], [1.0, 0.9, 0.2], [1.0, 0.9, 0.2], [1.0, 0.9, 0.2],
            # Face +Z (rouge)
            [1.0, 0.2, 0.2], [1.0, 0.2, 0.2], [1.0, 0.2, 0.2], [1.0, 0.2, 0.2],
            # Face -Z (rouge)
            [1.0, 0.2, 0.2], [1.0, 0.2, 0.2], [1.0, 0.2, 0.2], [1.0, 0.2, 0.2],
        ], dtype='f4')
        
        indices = np.array([
            # Face +X
            0, 1, 2,  0, 2, 3,
            # Face -X
            4, 5, 6,  4, 6, 7,
            # Face +Y
            8, 9, 10,  8, 10, 11,
            # Face -Y
            12, 13, 14,  12, 14, 15,
            # Face +Z
            16, 17, 18,  16, 18, 19,
            # Face -Z
            20, 21, 22,  20, 22, 23,
        ], dtype='i4')
        
        return vertices, colors, indices
    
    def create_axis_geometry(self, axis_length=1.2, labo_axis_length=2.5):
        """Crée la géométrie des axes."""
        # Axes du repère local (_mes) - rotatés avec le cube
        x_axis = np.array([[0, 0, 0], [axis_length, 0, 0]], dtype='f4')
        y_axis = np.array([[0, 0, 0], [0, axis_length, 0]], dtype='f4')
        z_axis = np.array([[0, 0, 0], [0, 0, axis_length]], dtype='f4')
        
        x_colors = np.array([[0.3, 0.6, 1.0], [0.3, 0.6, 1.0]], dtype='f4')  # Bleu
        y_colors = np.array([[1.0, 0.9, 0.2], [1.0, 0.9, 0.2]], dtype='f4')  # Jaune
        z_colors = np.array([[1.0, 0.2, 0.2], [1.0, 0.2, 0.2]], dtype='f4')  # Rouge
        
        # Axes du repère global (_labo) - fixes, plus grands et visibles
        # X vers la droite, Y vers le fond, Z vers le haut
        x_labo = np.array([[0, 0, 0], [labo_axis_length, 0, 0]], dtype='f4')
        y_labo = np.array([[0, 0, 0], [0, labo_axis_length, 0]], dtype='f4')
        z_labo = np.array([[0, 0, 0], [0, 0, labo_axis_length]], dtype='f4')
        # Couleurs plus vives pour le référentiel cartésien
        labo_x_color = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype='f4')  # Rouge pour X
        labo_y_color = np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]], dtype='f4')  # Vert pour Y
        labo_z_color = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], dtype='f4')  # Bleu pour Z
        
        return [
            (x_axis, x_colors, 'X_mes', True),
            (y_axis, y_colors, 'Y_mes', True),
            (z_axis, z_colors, 'Z_mes', True),
            (x_labo, labo_x_color, 'X_labo', False),
            (y_labo, labo_y_color, 'Y_labo', False),
            (z_labo, labo_z_color, 'Z_labo', False),
        ]
    
    def _create_grid(self, grid_size=5.0):
        """Crée la grille statique (non-rotée) au sol (plan XY, Z=0)."""
        grid_lines = []
        
        # Convertir grid_size en entier pour range()
        grid_size_int = int(grid_size)
        
        # Créer les lignes de la grille
        for i in range(-grid_size_int, grid_size_int + 1):
            # Lignes parallèles à X (constantes en Y)
            grid_lines.extend([[i, -grid_size, 0], [i, grid_size, 0]])
            # Lignes parallèles à Y (constantes en X)
            grid_lines.extend([[-grid_size, i, 0], [grid_size, i, 0]])
        
        vertices = np.array(grid_lines, dtype='f4')
        colors = np.array([[0.8, 0.8, 0.8]] * len(vertices), dtype='f4')  # Gris clair
        
        # Créer les VBOs et VAO
        vbo_v = self.ctx.buffer(vertices.tobytes())
        vbo_c = self.ctx.buffer(colors.tobytes())
        
        self.grid_vao = self.ctx.vertex_array(
            self.prog,
            [
                (vbo_v, '3f', 'in_position'),
                (vbo_c, '3f', 'in_color')
            ]
        )
    
    def create_vaos(self, vertices, colors, indices, axes_data):
        """Crée les VAOs pour le cube et les axes."""
        # Cube VAO
        vbo_vertices = self.ctx.buffer(vertices.tobytes())
        vbo_colors = self.ctx.buffer(colors.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())
        
        cube_vao = self.ctx.vertex_array(
            self.prog,
            [
                (vbo_vertices, '3f', 'in_position'),
                (vbo_colors, '3f', 'in_color'),
            ],
            index_buffer=ibo
        )
        
        # Axes VAOs
        axes_vaos = []
        for axis_vertices, axis_colors, name, is_rotated in axes_data:
            vbo_v = self.ctx.buffer(axis_vertices.tobytes())
            vbo_c = self.ctx.buffer(axis_colors.tobytes())
            vao = self.ctx.vertex_array(
                self.prog,
                [
                    (vbo_v, '3f', 'in_position'),
                    (vbo_c, '3f', 'in_color'),
                ]
            )
            axes_vaos.append((vao, name, is_rotated))
        
        return cube_vao, axes_vaos, len(indices)
    
    def render(self, mvp_matrix, model_matrix, cube_vao, axes_vaos, cube_indices_count):
        """Rendu de la scène en passes séparées."""
        self.ctx.clear(1.0, 1.0, 1.0)  # Fond blanc
        
        # Calculer la MVP pour le référentiel fixe (sans rotation du sensor)
        mvp_fixed = self._calculate_fixed_mvp(mvp_matrix)
        identity_matrix = Matrix44.identity()
        
        # 1. Grille statique (utilise MVP sans rotation model)
        self.ctx.line_width = 1.0
        self.prog['mvp'].write(mvp_fixed.astype('f4').tobytes())
        self.prog['model'].write(identity_matrix.astype('f4').tobytes())
        self.grid_vao.render(moderngl.LINES)
        
        # 2. Axes du référentiel fixe (_labo)
        self.ctx.line_width = 6.0  # Très épais pour bien les voir
        for vao, name, is_rotated in axes_vaos:
            if not is_rotated:  # Axes du référentiel fixe (_labo)
                self.prog['mvp'].write(mvp_fixed.astype('f4').tobytes())
                self.prog['model'].write(identity_matrix.astype('f4').tobytes())
                vao.render(moderngl.LINES)
        
        # 3. Cube roté
        self.ctx.line_width = 1.0
        self.prog['mvp'].write(mvp_matrix.astype('f4').tobytes())
        self.prog['model'].write(model_matrix.astype('f4').tobytes())
        cube_vao.render(moderngl.TRIANGLES)
        
        # 4. Axes du sensor (rotatés)
        self.ctx.line_width = 4.0  # Plus épais pour mieux voir
        for vao, name, is_rotated in axes_vaos:
            if is_rotated:  # Axes du sensor (_mes)
                self.prog['mvp'].write(mvp_matrix.astype('f4').tobytes())
                self.prog['model'].write(model_matrix.astype('f4').tobytes())
                vao.render(moderngl.LINES)
        self.ctx.line_width = 1.0
        
        glfw.swap_buffers(self.window)
    
    def _calculate_fixed_mvp(self, mvp_with_rotation):
        """Calcule la MVP pour le référentiel fixe (sans rotation du sensor)."""
        # Pour le référentiel fixe, on utilise la même MVP (projection + view)
        # mais on appliquera une matrice model identité dans le render
        # La MVP contient déjà projection * view, donc c'est correct
        return mvp_with_rotation
    
    def should_close(self):
        """Vérifie si la fenêtre doit être fermée."""
        return glfw.window_should_close(self.window)
    
    def poll_events(self):
        """Poll les événements GLFW."""
        glfw.poll_events()
    
    def update_window_title(self, sensor_angles: tuple, camera_angles: tuple):
        """Met à jour le titre de la fenêtre avec les angles."""
        theta_x, theta_y, theta_z = sensor_angles
        cam_x, cam_y, cam_dist = camera_angles
        title = f"Cube Sensor - Sensor: X={theta_x:.1f}° Y={theta_y:.1f}° Z={theta_z:.1f}° | Camera: Az={cam_x:.1f}° El={cam_y:.1f}° Dist={cam_dist:.1f}"
        glfw.set_window_title(self.window, title)
    
    def cleanup(self, cube_vao, axes_vaos):
        """Nettoie les ressources OpenGL."""
        cube_vao.release()
        for vao, _, _ in axes_vaos:
            vao.release()
        self.grid_vao.release()
        glfw.terminate()


class CubeSensorPresenter:
    """
    Presenter : Gère la logique métier et coordonne la View.
    Responsabilité : État de l'application, calculs de matrices, gestion des événements.
    """
    
    def __init__(self, view: CubeSensorView, sensor_orientation: SensorOrientation):
        self.view = view
        self.sensor_orientation = sensor_orientation
        self.camera_state = CameraState()
        
        # Créer les géométries
        vertices, colors, indices = view.create_cube_geometry(size=0.6)  # Cube plus petit
        axes_data = view.create_axis_geometry(axis_length=1.2, labo_axis_length=2.5)  # Axes plus longs
        
        # Créer les VAOs (la grille est créée dans _create_grid() de la View)
        self.cube_vao, self.axes_vaos, self.cube_indices_count = view.create_vaos(
            vertices, colors, indices, axes_data
        )
        
        # Connecter les callbacks
        view.setup_callbacks(self)
        
        # Calculer la matrice de rotation initiale
        self.model_matrix = sensor_orientation.to_rotation_matrix()
    
    def on_camera_rotate(self, dx: float, dy: float):
        """Gère la rotation de la caméra."""
        sensitivity = 0.5
        self.camera_state.angle_x += dx * sensitivity
        self.camera_state.angle_y += dy * sensitivity
        self.camera_state.angle_y = max(-89.0, min(89.0, self.camera_state.angle_y))
    
    def on_camera_zoom(self, yoffset: float):
        """Gère le zoom de la caméra."""
        zoom_factor = 1.1
        if yoffset > 0:
            self.camera_state.distance *= (1.0 / zoom_factor)
        elif yoffset < 0:
            self.camera_state.distance *= zoom_factor
        self.camera_state.distance = max(1.0, min(20.0, self.camera_state.distance))
    
    def on_key_press(self, key: int):
        """Gère les touches du clavier."""
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(self.view.window, True)
        elif key == glfw.KEY_EQUAL or key == glfw.KEY_KP_ADD:
            self.camera_state.distance *= 0.9
            self.camera_state.distance = max(1.0, min(20.0, self.camera_state.distance))
        elif key == glfw.KEY_MINUS or key == glfw.KEY_KP_SUBTRACT:
            self.camera_state.distance *= 1.1
            self.camera_state.distance = max(1.0, min(20.0, self.camera_state.distance))
        elif key == glfw.KEY_R:
            # Reset de la caméra
            self.camera_state = CameraState()
    
    def _calculate_mvp_matrix(self, use_model_rotation: bool = True) -> Matrix44:
        """Calcule la matrice Model-View-Projection."""
        # Projection
        aspect = self.view.width / self.view.height
        proj = Matrix44.perspective_projection(45.0, aspect, 0.1, 100.0)
        
        # Calculer la position de la caméra (coordonnées sphériques)
        import math as m
        angle_x_rad = m.radians(self.camera_state.angle_x)
        angle_y_rad = m.radians(self.camera_state.angle_y)
        
        cam_x = self.camera_state.distance * m.cos(angle_y_rad) * m.cos(angle_x_rad)
        cam_y = self.camera_state.distance * m.cos(angle_y_rad) * m.sin(angle_x_rad)
        cam_z = self.camera_state.distance * m.sin(angle_y_rad)
        
        camera_pos = Vector3([cam_x, cam_y, cam_z])
        
        # View (caméra)
        view = Matrix44.look_at(
            camera_pos,
            self.camera_state.target,
            Vector3([0.0, 0.0, 1.0])  # Up vector
        )
        
        # Model (rotation du sensor si demandé)
        if use_model_rotation:
            model = self.model_matrix
        else:
            model = Matrix44.identity()
        
        return proj * view * model
    
    def update(self):
        """Met à jour et rend la scène."""
        self.view.poll_events()
        
        # Mettre à jour le titre avec les angles
        sensor_angles = (
            self.sensor_orientation.theta_x_deg,
            self.sensor_orientation.theta_y_deg,
            self.sensor_orientation.theta_z_deg
        )
        camera_angles = (
            self.camera_state.angle_x,
            self.camera_state.angle_y,
            self.camera_state.distance
        )
        self.view.update_window_title(sensor_angles, camera_angles)
        
        # Calculer la matrice MVP (pour le cube et axes rotatés)
        mvp = self._calculate_mvp_matrix(use_model_rotation=True)
        
        # Rendre (la view gère le rendu en passes séparées)
        self.view.render(
            mvp,
            self.model_matrix,
            self.cube_vao,
            self.axes_vaos,
            self.cube_indices_count
        )
    
    def run(self):
        """Boucle principale."""
        while not self.view.should_close():
            self.update()
        
        # Nettoyage
        self.view.cleanup(self.cube_vao, self.axes_vaos, self.grid_vao)


def visualize_sensor_cube_modernGL(
    theta_x_deg: float = -45.0,
    theta_y_deg: float = None,
    theta_z_deg: float = 0.0
):
    """
    Visualise le cube sensor avec rotation physique - Version ModernGL.
    
    Args:
        theta_x_deg: Rotation autour de X en degrés (défaut: -45°)
        theta_y_deg: Rotation autour de Y en degrés (défaut: ~35.26°)
        theta_z_deg: Rotation autour de Z en degrés (défaut: 0°)
    """
    # Calculer theta_y par défaut si non fourni
    if theta_y_deg is None:
        theta_y_deg = math.degrees(math.atan(1 / math.sqrt(2)))  # ~35.26°
    
    # Créer l'orientation du sensor (Value Object)
    sensor_orientation = SensorOrientation(
        theta_x_deg=theta_x_deg,
        theta_y_deg=theta_y_deg,
        theta_z_deg=theta_z_deg
    )
    
    # Créer la View
    view = CubeSensorView(width=1024, height=768)
    
    # Créer le Presenter
    presenter = CubeSensorPresenter(view, sensor_orientation)
    
    print("Contrôles:")
    print("  Clic gauche + glisser : Rotation de la caméra")
    print("  Molette/Pinch : Zoom in/out")
    print("  +/- : Zoom in/out (clavier)")
    print("  R : Reset de la caméra")
    print("  ESC : Quitter")
    
    # Lancer la boucle principale
    presenter.run()


if __name__ == "__main__":
    visualize_sensor_cube_modernGL(
        theta_x_deg=-45.0,
        theta_y_deg=None,  # Sera calculé automatiquement (~35.26°)
        theta_z_deg=0.0
    )
