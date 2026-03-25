"""
CubeVisualizerAdapter — infrastructure/rendering layer.

Implements ICubeRenderer (outbound port) using PyVista.
Subscribes to EventBus for asynchronous updates from the application layer.
"""
import pyvista as pv
from typing import Optional
from PySide6.QtWidgets import QWidget
from scipy.spatial.transform import Rotation as R

from ...application.cube_visualizer_service.ports.i_cube_renderer import ICubeRenderer
from ..messaging.event_bus import EventBus, Event, EventType
from .cube_mesh_factory import create_colored_cube, apply_rotation_to_mesh


class CubeVisualizerAdapter(ICubeRenderer):
    """
    PyVista rendering adapter implementing ICubeRenderer.

    Manages a single PyVista plotter window and keeps it synchronized
    with the application layer via EventBus (ANGLES_CHANGED events).
    """

    CAMERA_POSITIONS = {
        '3d': ([(3, -3, 2), (0, 0, 0), (0, 0, 1)], 1.0),
        'xy': ([(0, 0, 3), (0, 0, 0), (0, 1, 0)], 0.8),
        'xz': ([(0, -3, 0), (0, 0, 0), (0, 0, 1)], 0.8),
        'yz': ([(3, 0, 0), (0, 0, 0), (0, 0, 1)], 0.8),
    }

    def __init__(self, event_bus: EventBus, parent_widget: Optional[QWidget] = None):
        self.event_bus = event_bus
        self.current_view = '3d'
        self.parent_widget = parent_widget
        self._last_rotation: Optional[R] = None

        self.plotter = None
        self.plotter_widget = None
        self.cube_actor = None
        self.arrows_mes: dict = {}
        self.arrows_labo: dict = {}
        self.text_actor = None

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_event)
        self.event_bus.subscribe(EventType.CAMERA_VIEW_CHANGED, self._on_camera_view_changed_event)

        self._create_plotter_standalone()

    # ---- ICubeRenderer implementation ----

    def update_view(self, rotation: R) -> None:
        """Render the cube with the given rotation."""
        if self.plotter is None:
            return
        self._last_rotation = rotation
        self._do_render(rotation)

    def reset_camera_view(self, view_name: str) -> None:
        if self.plotter is None:
            return
        try:
            pos, zoom = self.CAMERA_POSITIONS[view_name]
            self.plotter.camera_position = pos
            self.plotter.camera.zoom(zoom)
            self.current_view = view_name
            self.plotter.render()
        except Exception as e:
            print(f"[CubeVisualizerAdapter] reset_camera_view error: {e}")

    # ---- private ----

    def _create_plotter_standalone(self):
        self.plotter = pv.Plotter(title="Cube Sensor - Visualisation 3D")
        self.plotter_widget = None
        self._initialize_plotter()

        from PySide6.QtCore import QTimer
        def show_window():
            try:
                self.plotter.show(auto_close=False, interactive_update=True)
                QTimer.singleShot(200, lambda: self._do_initial_render())
                QTimer.singleShot(500, lambda: self._do_initial_render())
            except Exception as e:
                print(f"[CubeVisualizerAdapter] show_window error: {e}")

        QTimer.singleShot(300, show_window)

    def _initialize_plotter(self):
        if self.plotter is None:
            return
        self.plotter.set_background('white')
        self.plotter.show_grid()
        pos, zoom = self.CAMERA_POSITIONS['3d']
        self.plotter.camera_position = pos
        self.plotter.camera.zoom(zoom)
        self.plotter.enable_trackball_style()
        if hasattr(self.plotter, 'iren') and self.plotter.iren is not None:
            self.plotter.iren.add_observer('MouseWheelForwardEvent', self._on_wheel_forward)
            self.plotter.iren.add_observer('MouseWheelBackwardEvent', self._on_wheel_backward)

    def _do_initial_render(self):
        from ...domain.sensor_rotation import rotation_from_euler_xyz, get_default_theta_x, get_default_theta_y
        if self._last_rotation is None:
            self._last_rotation = rotation_from_euler_xyz(get_default_theta_x(), get_default_theta_y(), 0.0)
        self._do_render(self._last_rotation)

    def _do_render(self, rotation: R):
        if self.plotter is None:
            return
        try:
            # Clear old actors
            for actor in [self.cube_actor, self.text_actor,
                          *self.arrows_mes.values(), *self.arrows_labo.values()]:
                if actor is not None:
                    self.plotter.remove_actor(actor)
            self.arrows_mes.clear()
            self.arrows_labo.clear()

            # Cube
            cube = create_colored_cube(size=1.0)
            cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
            if "colors" in cube_rotated.cell_data:
                self.cube_actor = self.plotter.add_mesh(
                    cube_rotated, scalars="colors", rgb=True,
                    show_edges=True, edge_color='black', line_width=2)
            else:
                self.cube_actor = self.plotter.add_mesh(
                    cube_rotated, color='lightgray',
                    show_edges=True, edge_color='black', line_width=2)

            # Sensor axes (rotate with cube)
            axis_len, r = 2.0, 0.03
            for key, direction, color in [
                ('x', (1, 0, 0), '#4DA6FF'),
                ('y', (0, 1, 0), '#FFE633'),
                ('z', (0, 0, 1), '#FF3333'),
            ]:
                start = tuple(-d * axis_len / 2 for d in direction)
                arrow = pv.Arrow(start=start, direction=direction, scale=axis_len,
                                 tip_radius=r, tip_length=0.1, shaft_radius=r * 0.6)
                self.arrows_mes[key] = self.plotter.add_mesh(
                    apply_rotation_to_mesh(arrow, rotation), color=color)

            # Lab axes (fixed)
            lab_len, lr = 1.5, 0.03
            for key, direction, color in [
                ('x', (1, 0, 0), '#4DA6FF'),
                ('y', (0, 1, 0), '#FFE633'),
                ('z', (0, 0, 1), '#FF3333'),
            ]:
                arrow = pv.Arrow(start=(0, 0, 0), direction=direction, scale=lab_len,
                                 tip_radius=lr, tip_length=0.15, shaft_radius=lr * 0.6)
                self.arrows_labo[key] = self.plotter.add_mesh(arrow, color=color)

            euler = rotation.as_euler('XYZ', degrees=True)
            view_label = {'3d': 'Vue 3D', 'xy': 'Vue X-Y', 'xz': 'Vue X-Z', 'yz': 'Vue Y-Z'}
            self.text_actor = self.plotter.add_text(
                f"{view_label.get(self.current_view, '3D')} — "
                f"X={euler[0]:.1f}° Y={euler[1]:.1f}° Z={euler[2]:.1f}°",
                position='upper_left', font_size=12, color='black')

            self.plotter.render()
        except Exception as e:
            import traceback
            print(f"[CubeVisualizerAdapter] _do_render error: {e}")
            traceback.print_exc()

    def _on_angles_changed_event(self, event: Event):
        # EventBus already dispatches on the Qt main thread
        from ...domain.sensor_rotation import rotation_from_euler_xyz
        rotation = rotation_from_euler_xyz(
            event.data['theta_x'], event.data['theta_y'], event.data['theta_z'])
        self.update_view(rotation)

    def _on_camera_view_changed_event(self, event: Event):
        self.reset_camera_view(event.data.get('view_name', '3d'))

    def _on_wheel_forward(self, obj, event):
        if self.plotter and self.plotter.camera:
            self.plotter.camera.zoom(1.1)
            self.plotter.render()

    def _on_wheel_backward(self, obj, event):
        if self.plotter and self.plotter.camera:
            self.plotter.camera.zoom(0.9)
            self.plotter.render()
