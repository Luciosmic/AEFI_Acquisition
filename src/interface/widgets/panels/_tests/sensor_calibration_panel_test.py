import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from interface.widgets.panels.sensor_calibration_panel import SensorCalibrationPanel


class _FakeOrientationView(QWidget):
    def __init__(self):
        super().__init__()
        self.shown = []

    def show_orientation(self, theta_x, theta_y, theta_z):
        self.shown.append((theta_x, theta_y, theta_z))


def _active(theta_x, theta_y, theta_z):
    return SimpleNamespace(
        theta_x_degrees=theta_x, theta_y_degrees=theta_y, theta_z_degrees=theta_z,
        is_trial=True, is_calibrated=False, recorded_at=None,
    )


def test_active_rotation_is_forwarded_to_the_orientation_view():
    QApplication.instance() or QApplication([])
    view = _FakeOrientationView()
    panel = SensorCalibrationPanel(orientation_view=view)

    panel.on_active_rotation_updated(_active(35.3, 45.0, 1.0))

    assert view.shown == [(35.3, 45.0, 1.0)]
    assert panel.isAncestorOf(view)


def test_panel_works_without_orientation_view():
    QApplication.instance() or QApplication([])
    panel = SensorCalibrationPanel()
    panel.on_active_rotation_updated(_active(1.0, 2.0, 3.0))
    assert panel.spin_theta_z.value() == 3.0
