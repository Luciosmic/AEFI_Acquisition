"""
CubeSensorUI — interface/main.py

Entry point for the standalone cube visualizer application.
Wires up all layers: domain → application → infrastructure → interface.
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox, QMainWindow
)
from PySide6.QtCore import QTimer, Qt

try:
    from PySide6QtAds import CDockManager, CDockWidget, CenterDockWidgetArea
    QTADS_AVAILABLE = True
except ImportError:
    QTADS_AVAILABLE = False

from ..domain.sensor_rotation import get_default_theta_x, get_default_theta_y
from ..application.cube_visualizer_service.cube_visualizer_service import CubeVisualizerService
from ..infrastructure.messaging.command_bus import CommandBus
from ..infrastructure.messaging.event_bus import EventBus, Event, EventType
from ..infrastructure.rendering.cube_visualizer_adapter_pyvista import CubeVisualizerAdapter
from .cube_visualizer_presenter import CubeVisualizerPresenter


class CubeSensorUI(QMainWindow):
    """Qt window: wires all DDD layers and exposes the angle control UI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cube Sensor - Contrôle des Angles")
        self.setGeometry(100, 100, 500, 400)

        # ── Infrastructure ──────────────────────────────────────────────────
        self.command_bus = CommandBus()
        self.event_bus = EventBus()

        # ── Infrastructure / Rendering ──────────────────────────────────────
        self.adapter = CubeVisualizerAdapter(event_bus=self.event_bus)

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
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, self._on_angles_changed_event)

        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)

        # Angle controls
        angle_group = QGroupBox("Angles de Rotation du Sensor")
        ag_layout = QVBoxLayout(angle_group)

        self.spin_x = self._make_spinbox(get_default_theta_x(), ag_layout, "X (deg):")
        self.spin_y = self._make_spinbox(get_default_theta_y(), ag_layout, "Y (deg):")
        self.spin_z = self._make_spinbox(0.0, ag_layout, "Z (deg):")
        layout.addWidget(angle_group)

        # Camera view buttons
        view_group = QGroupBox("Vue caméra")
        vg_layout = QVBoxLayout(view_group)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for label, view in [("Vue 3D", "3d"), ("Vue XY", "xy")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=view: self.presenter.request_camera_view(v))
            row1.addWidget(btn)
        for label, view in [("Vue XZ", "xz"), ("Vue YZ", "yz")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=view: self.presenter.request_camera_view(v))
            row2.addWidget(btn)
        vg_layout.addLayout(row1)
        vg_layout.addLayout(row2)
        layout.addWidget(view_group)

        # Reset
        btn_reset = QPushButton("Reset (valeurs par défaut)")
        btn_reset.clicked.connect(self.presenter.request_reset)
        layout.addWidget(btn_reset)
        layout.addStretch()

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


def main():
    app = QApplication(sys.argv)
    window = CubeSensorUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
