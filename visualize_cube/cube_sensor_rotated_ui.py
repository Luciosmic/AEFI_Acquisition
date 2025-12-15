"""
Visualisation du cube sensor avec interface UI pour modifier les angles en temps réel.

Utilise PySide6 pour l'UI et PyVista pour la visualisation 3D.
Complexité : Faible-Moyenne (UI simple avec spinboxes + rafraîchissement du cube)
"""
import pyvista as pv
import numpy as np
from scipy.spatial.transform import Rotation as R
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox
)
from PySide6.QtCore import QTimer
import sys

# Importer les fonctions du script original
from cube_sensor_rotated import create_colored_cube, apply_rotation_to_mesh


class CubeSensorController:
    """Contrôleur qui gère les plotters PyVista et les mises à jour."""
    
    def __init__(self, ui_callback=None):
        """
        Args:
            ui_callback: Fonction appelée quand les angles changent depuis PyVista
                        Signature: callback(theta_x, theta_y, theta_z)
        """
        self.ui_callback = ui_callback
        
        # Vue principale (3D)
        self.plotter = pv.Plotter()
        self.plotter.set_background('white')
        self.plotter.show_grid()
        
        # Vues orthogonales : XY, XZ, YZ
        self.plotter_xy = pv.Plotter()
        self.plotter_xy.set_background('white')
        self.plotter_xy.show_grid()
        
        self.plotter_xz = pv.Plotter()
        self.plotter_xz.set_background('white')
        self.plotter_xz.show_grid()
        
        self.plotter_yz = pv.Plotter()
        self.plotter_yz.set_background('white')
        self.plotter_yz.show_grid()
        
        # Stocker les acteurs pour la vue principale
        self.cube_actor = None
        self.arrows_mes = {}
        self.arrows_labo = {}
        self.text_actor = None
        
        # Stocker les acteurs pour les vues orthogonales
        self.cube_actor_xy = None
        self.arrows_mes_xy = {}
        self.arrows_labo_xy = {}
        self.text_actor_xy = None
        
        self.cube_actor_xz = None
        self.arrows_mes_xz = {}
        self.arrows_labo_xz = {}
        self.text_actor_xz = None
        
        self.cube_actor_yz = None
        self.arrows_mes_yz = {}
        self.arrows_labo_yz = {}
        self.text_actor_yz = None
        
        # Widgets de contrôle dans les plotters
        self.slider_x = None
        self.slider_y = None
        self.slider_z = None
        self.slider_x_xy = None
        self.slider_y_xy = None
        self.slider_z_xy = None
        self.slider_x_xz = None
        self.slider_y_xz = None
        self.slider_z_xz = None
        self.slider_x_yz = None
        self.slider_y_yz = None
        self.slider_z_yz = None
        
        # Valeurs actuelles
        self.theta_x = 0.0
        self.theta_y = math.degrees(math.atan(1 / math.sqrt(2)))  # ~35.26°
        self.theta_z = 0.0
        
        # Initialiser les visualisations
        self._update_visualization()
        
        # Position de caméra vue principale
        self.plotter.camera_position = [(3, -3, 2), (0, 0, 0), (0, 0, 1)]
        
        # Positions de caméra pour les vues orthogonales
        # Vue XY : regarde depuis Z positif (vers le bas)
        self.plotter_xy.camera_position = [(0, 0, 3), (0, 0, 0), (0, 1, 0)]
        self.plotter_xy.camera.zoom(0.8)
        
        # Vue XZ : regarde depuis Y négatif (Y vers le fond)
        self.plotter_xz.camera_position = [(0, -3, 0), (0, 0, 0), (0, 0, 1)]
        self.plotter_xz.camera.zoom(0.8)
        
        # Vue YZ : regarde depuis X positif (X vers la droite)
        self.plotter_yz.camera_position = [(3, 0, 0), (0, 0, 0), (0, 0, 1)]
        self.plotter_yz.camera.zoom(0.8)
        
        # Activer le zoom au touchpad (pincement) pour tous les plotters
        # PyVista active cela par défaut avec enable_trackball_style()
        for plotter in [self.plotter, self.plotter_xy, self.plotter_xz, self.plotter_yz]:
            plotter.enable_trackball_style()  # Active les interactions incluant le zoom au touchpad
            # Le zoom au pincement est activé par défaut avec trackball style
        
        # Ajouter les widgets de contrôle dans les plotters
        self._add_control_widgets()
    
    def _update_visualization(self):
        """Met à jour toute la visualisation avec les angles actuels."""
        # Créer la rotation
        rotation = R.from_euler('xyz', [self.theta_x, self.theta_y, self.theta_z], degrees=True)
        
        # Mettre à jour la vue principale
        self._update_main_view(rotation)
        
        # Mettre à jour les vues orthogonales
        self._update_xy_view(rotation)
        self._update_xz_view(rotation)
        self._update_yz_view(rotation)
    
    def _update_main_view(self, rotation):
        """Met à jour la vue principale 3D."""
        # Supprimer les anciens éléments
        if self.cube_actor is not None:
            self.plotter.remove_actor(self.cube_actor)
        for arrow in self.arrows_mes.values():
            self.plotter.remove_actor(arrow)
        for arrow in self.arrows_labo.values():
            self.plotter.remove_actor(arrow)
        if self.text_actor is not None:
            self.plotter.remove_actor(self.text_actor)
        
        self.arrows_mes.clear()
        self.arrows_labo.clear()
        
        # Créer et ajouter le cube
        cube = create_colored_cube(size=1.0)
        cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
        
        if "colors" in cube_rotated.cell_data:
            self.cube_actor = self.plotter.add_mesh(
                cube_rotated,
                scalars="colors",
                rgb=True,
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        else:
            self.cube_actor = self.plotter.add_mesh(
                cube_rotated,
                color='lightgray',
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        
        # Ajouter les axes du repère local (_mes)
        axis_length = 0.8
        arrow_radius = 0.05
        
        # X_mes (Bleu) - à rotation 0° aligné avec X_labo (bleu)
        arrow_x = pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes['x'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_x, rotation), color='#4DA6FF')
        
        # Y_mes (Jaune) - à rotation 0° aligné avec Y_labo (jaune)
        arrow_y = pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes['y'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_y, rotation), color='#FFE633')
        
        # Z_mes (Rouge) - à rotation 0° aligné avec Z_labo (rouge)
        arrow_z = pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes['z'] = self.plotter.add_mesh(apply_rotation_to_mesh(arrow_z, rotation), color='#FF3333')
        
        # Ajouter les axes du repère global (_labo) - fixes
        # X_labo = Bleu, Y_labo = Jaune, Z_labo = Rouge
        labo_axis_length = 1.5
        labo_arrow_radius = 0.03
        
        self.arrows_labo['x'] = self.plotter.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#4DA6FF'  # Bleu
        )
        self.arrows_labo['y'] = self.plotter.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FFE633'  # Jaune
        )
        self.arrows_labo['z'] = self.plotter.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FF3333'  # Rouge
        )
        
        # Ajouter le texte avec les angles
        self.text_actor = self.plotter.add_text(
            f"Vue 3D - Rotation: X={self.theta_x:.1f}° Y={self.theta_y:.1f}° Z={self.theta_z:.1f}°",
            position='upper_left',
            font_size=12,
            color='black'
        )
        
        # Rafraîchir le rendu
        self.plotter.render()
    
    def _update_xz_view(self, rotation):
        """Met à jour la vue plan X-Z (Y vers le fond)."""
        # Supprimer les anciens éléments
        if self.cube_actor_xz is not None:
            self.plotter_xz.remove_actor(self.cube_actor_xz)
        for arrow in self.arrows_mes_xz.values():
            self.plotter_xz.remove_actor(arrow)
        for arrow in self.arrows_labo_xz.values():
            self.plotter_xz.remove_actor(arrow)
        if self.text_actor_xz is not None:
            self.plotter_xz.remove_actor(self.text_actor_xz)
        
        self.arrows_mes_xz.clear()
        self.arrows_labo_xz.clear()
        
        # Créer et ajouter le cube
        cube = create_colored_cube(size=1.0)
        cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
        
        if "colors" in cube_rotated.cell_data:
            self.cube_actor_xz = self.plotter_xz.add_mesh(
                cube_rotated,
                scalars="colors",
                rgb=True,
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        else:
            self.cube_actor_xz = self.plotter_xz.add_mesh(
                cube_rotated,
                color='lightgray',
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        
        # Ajouter les axes du repère local (_mes)
        axis_length = 0.8
        arrow_radius = 0.05
        
        # X_mes (Bleu)
        arrow_x = pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xz['x'] = self.plotter_xz.add_mesh(apply_rotation_to_mesh(arrow_x, rotation), color='#4DA6FF')
        
        # Y_mes (Jaune) - visible en projection
        arrow_y = pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xz['y'] = self.plotter_xz.add_mesh(apply_rotation_to_mesh(arrow_y, rotation), color='#FFE633')
        
        # Z_mes (Rouge)
        arrow_z = pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xz['z'] = self.plotter_xz.add_mesh(apply_rotation_to_mesh(arrow_z, rotation), color='#FF3333')
        
        # Ajouter les axes du repère global (_labo) - fixes
        labo_axis_length = 1.5
        labo_arrow_radius = 0.03
        
        self.arrows_labo_xz['x'] = self.plotter_xz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#4DA6FF'  # Bleu
        )
        self.arrows_labo_xz['y'] = self.plotter_xz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FFE633'  # Jaune
        )
        self.arrows_labo_xz['z'] = self.plotter_xz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FF3333'  # Rouge
        )
        
        # Ajouter le texte avec les angles
        self.text_actor_xz = self.plotter_xz.add_text(
            f"Vue X-Z (Y vers fond) - Rotation: X={self.theta_x:.1f}° Y={self.theta_y:.1f}° Z={self.theta_z:.1f}°",
            position='upper_left',
            font_size=12,
            color='black'
        )
        
        # Rafraîchir le rendu
        self.plotter_xz.render()
    
    def _update_xy_view(self, rotation):
        """Met à jour la vue plan X-Y (Z vers le haut)."""
        # Supprimer les anciens éléments
        if self.cube_actor_xy is not None:
            self.plotter_xy.remove_actor(self.cube_actor_xy)
        for arrow in self.arrows_mes_xy.values():
            self.plotter_xy.remove_actor(arrow)
        for arrow in self.arrows_labo_xy.values():
            self.plotter_xy.remove_actor(arrow)
        if self.text_actor_xy is not None:
            self.plotter_xy.remove_actor(self.text_actor_xy)
        
        self.arrows_mes_xy.clear()
        self.arrows_labo_xy.clear()
        
        # Créer et ajouter le cube
        cube = create_colored_cube(size=1.0)
        cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
        
        if "colors" in cube_rotated.cell_data:
            self.cube_actor_xy = self.plotter_xy.add_mesh(
                cube_rotated,
                scalars="colors",
                rgb=True,
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        else:
            self.cube_actor_xy = self.plotter_xy.add_mesh(
                cube_rotated,
                color='lightgray',
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        
        # Ajouter les axes du repère local (_mes)
        axis_length = 0.8
        arrow_radius = 0.05
        
        arrow_x = pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xy['x'] = self.plotter_xy.add_mesh(apply_rotation_to_mesh(arrow_x, rotation), color='#4DA6FF')
        
        arrow_y = pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xy['y'] = self.plotter_xy.add_mesh(apply_rotation_to_mesh(arrow_y, rotation), color='#FFE633')
        
        arrow_z = pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_xy['z'] = self.plotter_xy.add_mesh(apply_rotation_to_mesh(arrow_z, rotation), color='#FF3333')
        
        # Ajouter les axes du repère global (_labo) - fixes
        labo_axis_length = 1.5
        labo_arrow_radius = 0.03
        
        self.arrows_labo_xy['x'] = self.plotter_xy.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#4DA6FF'
        )
        self.arrows_labo_xy['y'] = self.plotter_xy.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FFE633'
        )
        self.arrows_labo_xy['z'] = self.plotter_xy.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FF3333'
        )
        
        self.text_actor_xy = self.plotter_xy.add_text(
            f"Vue X-Y (Z vers haut) - Rotation: X={self.theta_x:.1f}° Y={self.theta_y:.1f}° Z={self.theta_z:.1f}°",
            position='upper_left',
            font_size=12,
            color='black'
        )
        
        self.plotter_xy.render()
    
    def _update_yz_view(self, rotation):
        """Met à jour la vue plan Y-Z (X vers la droite)."""
        # Supprimer les anciens éléments
        if self.cube_actor_yz is not None:
            self.plotter_yz.remove_actor(self.cube_actor_yz)
        for arrow in self.arrows_mes_yz.values():
            self.plotter_yz.remove_actor(arrow)
        for arrow in self.arrows_labo_yz.values():
            self.plotter_yz.remove_actor(arrow)
        if self.text_actor_yz is not None:
            self.plotter_yz.remove_actor(self.text_actor_yz)
        
        self.arrows_mes_yz.clear()
        self.arrows_labo_yz.clear()
        
        # Créer et ajouter le cube
        cube = create_colored_cube(size=1.0)
        cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
        
        if "colors" in cube_rotated.cell_data:
            self.cube_actor_yz = self.plotter_yz.add_mesh(
                cube_rotated,
                scalars="colors",
                rgb=True,
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        else:
            self.cube_actor_yz = self.plotter_yz.add_mesh(
                cube_rotated,
                color='lightgray',
                show_edges=True,
                edge_color='black',
                line_width=2,
                opacity=1.0
            )
        
        # Ajouter les axes du repère local (_mes)
        axis_length = 0.8
        arrow_radius = 0.05
        
        arrow_x = pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_yz['x'] = self.plotter_yz.add_mesh(apply_rotation_to_mesh(arrow_x, rotation), color='#4DA6FF')
        
        arrow_y = pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_yz['y'] = self.plotter_yz.add_mesh(apply_rotation_to_mesh(arrow_y, rotation), color='#FFE633')
        
        arrow_z = pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=axis_length,
                          tip_radius=arrow_radius, tip_length=0.2, shaft_radius=arrow_radius * 0.6)
        self.arrows_mes_yz['z'] = self.plotter_yz.add_mesh(apply_rotation_to_mesh(arrow_z, rotation), color='#FF3333')
        
        # Ajouter les axes du repère global (_labo) - fixes
        labo_axis_length = 1.5
        labo_arrow_radius = 0.03
        
        self.arrows_labo_yz['x'] = self.plotter_yz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(1, 0, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#4DA6FF'
        )
        self.arrows_labo_yz['y'] = self.plotter_yz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 1, 0), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FFE633'
        )
        self.arrows_labo_yz['z'] = self.plotter_yz.add_mesh(
            pv.Arrow(start=(0, 0, 0), direction=(0, 0, 1), scale=labo_axis_length,
                    tip_radius=labo_arrow_radius, tip_length=0.15, shaft_radius=labo_arrow_radius * 0.6),
            color='#FF3333'
        )
        
        self.text_actor_yz = self.plotter_yz.add_text(
            f"Vue Y-Z (X vers droite) - Rotation: X={self.theta_x:.1f}° Y={self.theta_y:.1f}° Z={self.theta_z:.1f}°",
            position='upper_left',
            font_size=12,
            color='black'
        )
        
        self.plotter_yz.render()
    
    def _add_control_widgets(self):
        """Ajoute des sliders pour contrôler les angles dans les plotters."""
        # Sliders pour la vue principale
        self.slider_x = self.plotter.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_x,
            title="X (deg)",
            pointa=(0.02, 0.9),
            pointb=(0.3, 0.9),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_y = self.plotter.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_y,
            title="Y (deg)",
            pointa=(0.02, 0.8),
            pointb=(0.3, 0.8),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_z = self.plotter.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_z,
            title="Z (deg)",
            pointa=(0.02, 0.7),
            pointb=(0.3, 0.7),
            style='modern',
            interaction_event='always'
        )
        
        # Sliders pour la vue X-Z
        self.slider_x_xz = self.plotter_xz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_x,
            title="X (deg)",
            pointa=(0.02, 0.9),
            pointb=(0.3, 0.9),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_y_xz = self.plotter_xz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_y,
            title="Y (deg)",
            pointa=(0.02, 0.8),
            pointb=(0.3, 0.8),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_z_xz = self.plotter_xz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_z,
            title="Z (deg)",
            pointa=(0.02, 0.7),
            pointb=(0.3, 0.7),
            style='modern',
            interaction_event='always'
        )
        
        # Sliders pour la vue XY
        self.slider_x_xy = self.plotter_xy.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_x,
            title="X (deg)",
            pointa=(0.02, 0.9),
            pointb=(0.3, 0.9),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_y_xy = self.plotter_xy.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_y,
            title="Y (deg)",
            pointa=(0.02, 0.8),
            pointb=(0.3, 0.8),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_z_xy = self.plotter_xy.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_z,
            title="Z (deg)",
            pointa=(0.02, 0.7),
            pointb=(0.3, 0.7),
            style='modern',
            interaction_event='always'
        )
        
        # Sliders pour la vue YZ
        self.slider_x_yz = self.plotter_yz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_x,
            title="X (deg)",
            pointa=(0.02, 0.9),
            pointb=(0.3, 0.9),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_y_yz = self.plotter_yz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_y,
            title="Y (deg)",
            pointa=(0.02, 0.8),
            pointb=(0.3, 0.8),
            style='modern',
            interaction_event='always'
        )
        
        self.slider_z_yz = self.plotter_yz.add_slider_widget(
            callback=self._on_slider_changed,
            rng=(-180, 180),
            value=self.theta_z,
            title="Z (deg)",
            pointa=(0.02, 0.7),
            pointb=(0.3, 0.7),
            style='modern',
            interaction_event='always'
        )
    
    def _on_slider_changed(self, value):
        """Callback appelé quand un slider change dans n'importe quel plotter."""
        # Récupérer les valeurs de tous les sliders (ils sont synchronisés)
        if self.slider_x is not None:
            self.theta_x = self.slider_x.GetRepresentation().GetValue()
        if self.slider_y is not None:
            self.theta_y = self.slider_y.GetRepresentation().GetValue()
        if self.slider_z is not None:
            self.theta_z = self.slider_z.GetRepresentation().GetValue()
        
        # Synchroniser tous les sliders
        if self.slider_x_xy is not None:
            self.slider_x_xy.GetRepresentation().SetValue(self.theta_x)
        if self.slider_y_xy is not None:
            self.slider_y_xy.GetRepresentation().SetValue(self.theta_y)
        if self.slider_z_xy is not None:
            self.slider_z_xy.GetRepresentation().SetValue(self.theta_z)
        if self.slider_x_xz is not None:
            self.slider_x_xz.GetRepresentation().SetValue(self.theta_x)
        if self.slider_y_xz is not None:
            self.slider_y_xz.GetRepresentation().SetValue(self.theta_y)
        if self.slider_z_xz is not None:
            self.slider_z_xz.GetRepresentation().SetValue(self.theta_z)
        if self.slider_x_yz is not None:
            self.slider_x_yz.GetRepresentation().SetValue(self.theta_x)
        if self.slider_y_yz is not None:
            self.slider_y_yz.GetRepresentation().SetValue(self.theta_y)
        if self.slider_z_yz is not None:
            self.slider_z_yz.GetRepresentation().SetValue(self.theta_z)
        
        # Mettre à jour la visualisation
        self._update_visualization()
        
        # Notifier l'UI si callback fourni
        if self.ui_callback:
            self.ui_callback(self.theta_x, self.theta_y, self.theta_z)
    
    def update_angles(self, theta_x, theta_y, theta_z):
        """Met à jour les angles et rafraîchit la visualisation."""
        self.theta_x = theta_x
        self.theta_y = theta_y
        self.theta_z = theta_z
        
        # Mettre à jour les sliders
        if self.slider_x is not None:
            self.slider_x.GetRepresentation().SetValue(theta_x)
        if self.slider_y is not None:
            self.slider_y.GetRepresentation().SetValue(theta_y)
        if self.slider_z is not None:
            self.slider_z.GetRepresentation().SetValue(theta_z)
        if self.slider_x_xy is not None:
            self.slider_x_xy.GetRepresentation().SetValue(theta_x)
        if self.slider_y_xy is not None:
            self.slider_y_xy.GetRepresentation().SetValue(theta_y)
        if self.slider_z_xy is not None:
            self.slider_z_xy.GetRepresentation().SetValue(theta_z)
        if self.slider_x_xz is not None:
            self.slider_x_xz.GetRepresentation().SetValue(theta_x)
        if self.slider_y_xz is not None:
            self.slider_y_xz.GetRepresentation().SetValue(theta_y)
        if self.slider_z_xz is not None:
            self.slider_z_xz.GetRepresentation().SetValue(theta_z)
        if self.slider_x_yz is not None:
            self.slider_x_yz.GetRepresentation().SetValue(theta_x)
        if self.slider_y_yz is not None:
            self.slider_y_yz.GetRepresentation().SetValue(theta_y)
        if self.slider_z_yz is not None:
            self.slider_z_yz.GetRepresentation().SetValue(theta_z)
        
        self._update_visualization()
    
    def show(self):
        """Affiche les fenêtres PyVista sur le thread principal."""
        # Toutes les fenêtres doivent être ouvertes sur le thread principal (macOS requirement)
        # On les ouvre directement - PyVista gère plusieurs fenêtres
        self.plotter.show(auto_close=False, interactive_update=True)
        self.plotter_xy.show(auto_close=False, interactive_update=True)
        self.plotter_xz.show(auto_close=False, interactive_update=True)
        self.plotter_yz.show(auto_close=False, interactive_update=True)


class CubeSensorUI(QWidget):
    """Fenêtre UI simple pour contrôler les angles."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cube Sensor - Contrôle des Angles")
        self.setGeometry(100, 100, 350, 200)
        
        layout = QVBoxLayout(self)
        
        # Groupe pour les angles
        group = QGroupBox("Angles de Rotation du Sensor")
        group_layout = QVBoxLayout(group)
        
        # Angle X
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X (deg):"))
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-180.0, 180.0)
        self.spin_x.setValue(0.0)
        self.spin_x.setDecimals(1)
        self.spin_x.setSingleStep(1.0)
        self.spin_x.valueChanged.connect(self._on_angle_changed)
        x_layout.addWidget(self.spin_x)
        group_layout.addLayout(x_layout)
        
        # Angle Y
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y (deg):"))
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-180.0, 180.0)
        self.spin_y.setValue(math.degrees(math.atan(1 / math.sqrt(2))))
        self.spin_y.setDecimals(1)
        self.spin_y.setSingleStep(1.0)
        self.spin_y.valueChanged.connect(self._on_angle_changed)
        y_layout.addWidget(self.spin_y)
        group_layout.addLayout(y_layout)
        
        # Angle Z
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z (deg):"))
        self.spin_z = QDoubleSpinBox()
        self.spin_z.setRange(-180.0, 180.0)
        self.spin_z.setValue(0.0)
        self.spin_z.setDecimals(1)
        self.spin_z.setSingleStep(1.0)
        self.spin_z.valueChanged.connect(self._on_angle_changed)
        z_layout.addWidget(self.spin_z)
        group_layout.addLayout(z_layout)
        
        layout.addWidget(group)
        
        # Bouton Reset
        btn_reset = QPushButton("Reset (Cube par défaut)")
        btn_reset.clicked.connect(self._on_reset)
        layout.addWidget(btn_reset)
        
        # Contrôleur PyVista avec callback pour synchroniser l'UI
        self.controller = CubeSensorController(ui_callback=self._on_angles_changed_from_pyvista)
        
        # Timer pour éviter trop de rafraîchissements
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._do_update)
        self.update_timer.setSingleShot(True)
        
        # Flag pour éviter les boucles de mise à jour
        self._updating_from_pyvista = False
    
    def _on_angle_changed(self):
        """Appelé quand un angle change depuis l'UI - déclenche un update avec délai."""
        if self._updating_from_pyvista:
            return  # Éviter les boucles
        self.update_timer.stop()
        self.update_timer.start(150)  # 150ms de délai
    
    def _do_update(self):
        """Effectue la mise à jour de la visualisation depuis l'UI."""
        theta_x = self.spin_x.value()
        theta_y = self.spin_y.value()
        theta_z = self.spin_z.value()
        self.controller.update_angles(theta_x, theta_y, theta_z)
    
    def _on_angles_changed_from_pyvista(self, theta_x, theta_y, theta_z):
        """Callback appelé quand les angles changent depuis PyVista."""
        self._updating_from_pyvista = True
        self.spin_x.setValue(theta_x)
        self.spin_y.setValue(theta_y)
        self.spin_z.setValue(theta_z)
        self._updating_from_pyvista = False
    
    def _on_reset(self):
        """Reset aux valeurs par défaut."""
        self.spin_x.setValue(0.0)
        self.spin_y.setValue(math.degrees(math.atan(1 / math.sqrt(2))))
        self.spin_z.setValue(0.0)
    
    def showEvent(self, event):
        """Affiche les fenêtres PyVista après que la fenêtre Qt soit affichée."""
        super().showEvent(event)
        # Utiliser un timer pour différer l'ouverture de PyVista (sur le thread principal)
        QTimer.singleShot(200, self.controller.show)


def main():
    """Point d'entrée principal."""
    app = QApplication(sys.argv)
    
    window = CubeSensorUI()
    window.show()  # Afficher la fenêtre Qt en premier
    
    print("Fenêtre UI ouverte. Modifiez les angles pour voir le cube se mettre à jour.")
    print("(La fenêtre PyVista s'ouvrira automatiquement après l'UI)")
    
    # Lancer la boucle d'événements Qt
    # La fenêtre PyVista s'ouvrira via showEvent après que Qt soit prêt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

