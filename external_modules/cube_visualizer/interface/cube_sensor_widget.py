"""
CubeSensorWidget — interface layer.

Embeddable composition root: wires domain → application → infrastructure →
interface and shows angle controls next to the 3D view.
See cube_sensor_widget_intention.md.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox,
)
from PySide6.QtCore import QCoreApplication, QTimer, Qt
from PySide6.QtGui import QSurfaceFormat
from pyvistaqt.rwi import _default_format  # ponytail: private, the exact format QtInteractor installs

from ..domain.sensor_rotation import get_default_theta_x, get_default_theta_y
from ..application.cube_visualizer_service.cube_visualizer_service import CubeVisualizerService
from ..infrastructure.messaging.command_bus import CommandBus
from ..infrastructure.messaging.event_bus import EventBus, Event, EventType
from ..infrastructure.rendering.cube_visualizer_adapter_pyvista import CubeVisualizerAdapter
from .cube_visualizer_presenter import CubeVisualizerPresenter


def configure_qt_opengl() -> None:
    """Call before QApplication() in any host that opens another top-level
    window before this widget, or that floats it (QtAds docks): without it
    the 3D view composites black."""
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QSurfaceFormat.setDefaultFormat(_default_format())


class CubeSensorWidget(QWidget):
    """Angle controls + embedded 3D view of the sensor cube."""

    def __init__(self, parent=None, angle_controls: bool = True):
        super().__init__(parent)
        self._angle_controls = angle_controls

        # ── Infrastructure ──────────────────────────────────────────────────
        self.command_bus = CommandBus()
        self.event_bus = EventBus()

        # ── Infrastructure / Rendering ──────────────────────────────────────
        self.adapter = CubeVisualizerAdapter(event_bus=self.event_bus, parent_widget=self)

        # ── Application ─────────────────────────────────────────────────────
        self.service = CubeVisualizerService(renderer=self.adapter)

        # ── Interface / Presenter ───────────────────────────────────────────
        self.presenter = CubeVisualizerPresenter(
            service=self.service,
            command_bus=self.command_bus,
            event_bus=self.event_bus,
        )

        # ── UI ───────────────────────────────────────────────────────────────
        self._updating_from_event = False
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_event)

        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Left: angle controls (hidden when the host owns the angles)
        controls = QWidget()
        controls.setMaximumWidth(260)
        controls.setVisible(self._angle_controls)
        c_layout = QVBoxLayout(controls)
        c_layout.setContentsMargins(0, 0, 0, 0)

        angle_group = QGroupBox("Angles de Rotation du Sensor")
        ag_layout = QVBoxLayout(angle_group)
        self.spin_x = self._make_spinbox(get_default_theta_x(), ag_layout, "X (deg):")
        self.spin_y = self._make_spinbox(get_default_theta_y(), ag_layout, "Y (deg):")
        self.spin_z = self._make_spinbox(0.0, ag_layout, "Z (deg):")
        c_layout.addWidget(angle_group)

        btn_reset = QPushButton("Reset (valeurs par défaut)")
        btn_reset.clicked.connect(self.presenter.request_reset)
        c_layout.addWidget(btn_reset)
        c_layout.addStretch()

        # Right: one row of camera-view buttons above the 3D view
        right = QVBoxLayout()
        views = QHBoxLayout()
        for label, view in (("Vue 3D", "3d"), ("Vue XY", "xy"), ("Vue XZ", "xz"), ("Vue YZ", "yz")):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=view: self.presenter.request_camera_view(v))
            views.addWidget(btn)
        right.addLayout(views)
        right.addWidget(self.adapter.widget, 1)

        layout.addWidget(controls)
        layout.addLayout(right, 1)

    def _make_spinbox(self, default_value: float, parent_layout, label: str) -> QDoubleSpinBox:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        spin = QDoubleSpinBox()
        spin.setRange(-180.0, 180.0)
        spin.setValue(default_value)
        spin.setDecimals(1)
        spin.setSingleStep(1.0)
        spin.valueChanged.connect(self._on_angle_changed)
        row.addWidget(spin)
        parent_layout.addLayout(row)
        return spin

    # ── Host API ─────────────────────────────────────────────────────────────

    def show_orientation(self, theta_x: float, theta_y: float, theta_z: float) -> None:
        """Drive the orientation from a host that owns the angles."""
        self.presenter.request_update_angles(theta_x=theta_x, theta_y=theta_y, theta_z=theta_z)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_angle_changed(self):
        if self._updating_from_event:
            return
        self.update_timer.stop()
        self.update_timer.start(150)

    def _do_update(self):
        self.presenter.request_update_angles(
            theta_x=self.spin_x.value(),
            theta_y=self.spin_y.value(),
            theta_z=self.spin_z.value(),
        )

    def _on_angles_changed_event(self, event: Event):
        """Sync spinboxes when state changes (e.g. after reset)."""
        self._updating_from_event = True
        self.spin_x.setValue(event.data['theta_x'])
        self.spin_y.setValue(event.data['theta_y'])
        self.spin_z.setValue(event.data['theta_z'])
        self._updating_from_event = False
