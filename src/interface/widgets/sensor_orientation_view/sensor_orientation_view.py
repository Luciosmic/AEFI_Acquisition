"""
Sensor Orientation View

3D cube of the sensor, drawn for a given mounting matrix P.
See sensor_orientation_view_intention.md.
"""
import pyvista as pv
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor
from pyvistaqt.rwi import _default_format  # ponytail: private, the exact format QtInteractor installs

from interface.widgets.sensor_orientation_view.cube_mesh_factory import (
    MARKER_COLOR,
    apply_mounting_matrix,
    create_colored_cube,
    create_negative_face_markers,
)

_IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
# (key, direction, color) — same colors as the cube faces
_AXES = (('x', (1, 0, 0), '#4DA6FF'), ('y', (0, 1, 0), '#FFE633'), ('z', (0, 0, 1), '#FF3333'))


def configure_qt_opengl() -> None:
    """Call before QApplication(): without it the 3D view composites black
    behind a splash window or in a floating dock (see intention)."""
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QSurfaceFormat.setDefaultFormat(_default_format())


class SensorOrientationView(QWidget):
    """Camera-view buttons above an embedded 3D view of the sensor cube."""

    CAMERA_POSITIONS = {
        '3d': ([(3, -3, 2), (0, 0, 0), (0, 0, 1)], 1.0),
        'xy': ([(0, 0, 3), (0, 0, 0), (0, 1, 0)], 0.8),
        'xz': ([(0, -3, 0), (0, 0, 0), (0, 0, 1)], 0.8),
        'yz': ([(3, 0, 0), (0, 0, 0), (0, 0, 1)], 0.8),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cube_actor = None
        self.marker_actor = None
        self.arrows_sensor: dict = {}
        self.arrows_sources: dict = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        views = QHBoxLayout()
        for label, view in (("Vue 3D", "3d"), ("Vue XY", "xy"), ("Vue XZ", "xz"), ("Vue YZ", "yz")):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=view: self.set_camera_view(v))
            views.addWidget(btn)
        layout.addLayout(views)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter, 1)
        self.plotter.set_background('white')
        self.plotter.show_grid()
        self.plotter.enable_trackball_style()
        self.set_camera_view('3d')
        self.show_mounting(_IDENTITY)  # never shown empty; the host feeds the active P

    def show_mounting(self, matrix) -> None:
        """Redraw the cube for the mounting matrix P (rows; columns = sensor axes in sources frame)."""
        for actor in (self.cube_actor, self.marker_actor,
                      *self.arrows_sensor.values(), *self.arrows_sources.values()):
            if actor is not None:
                self.plotter.remove_actor(actor)
        self.arrows_sensor.clear()
        self.arrows_sources.clear()

        self.cube_actor = self.plotter.add_mesh(
            apply_mounting_matrix(create_colored_cube(size=1.0), matrix),
            scalars="colors", rgb=True, show_edges=True, edge_color='black', line_width=2)
        self.marker_actor = self.plotter.add_mesh(
            apply_mounting_matrix(create_negative_face_markers(size=1.0), matrix), color=MARKER_COLOR)

        # Sensor-frame axes (rotate with the cube), through the cube
        axis_len, r = 2.0, 0.03
        for key, direction, color in _AXES:
            start = tuple(-d * axis_len / 2 for d in direction)
            arrow = pv.Arrow(start=start, direction=direction, scale=axis_len,
                             tip_radius=r, tip_length=0.1, shaft_radius=r * 0.6)
            self.arrows_sensor[key] = self.plotter.add_mesh(apply_mounting_matrix(arrow, matrix), color=color)

        # Sources-frame axes (fixed)
        sources_len, sr = 1.5, 0.03
        for key, direction, color in _AXES:
            arrow = pv.Arrow(start=(0, 0, 0), direction=direction, scale=sources_len,
                             tip_radius=sr, tip_length=0.15, shaft_radius=sr * 0.6)
            self.arrows_sources[key] = self.plotter.add_mesh(arrow, color=color)

        self.plotter.render()

    def set_camera_view(self, view_name: str) -> None:
        position, zoom = self.CAMERA_POSITIONS[view_name]
        self.plotter.camera_position = position
        self.plotter.camera.zoom(zoom)
        self.plotter.render()
