import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QWidget

from interface.widgets.panels.sensor_calibration_panel import SensorCalibrationPanel

_P = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


class _FakeOrientationView(QWidget):
    def __init__(self):
        super().__init__()
        self.shown = []

    def show_mounting(self, matrix):
        self.shown.append(matrix)


def _active(theta_x, theta_y, theta_z):
    return SimpleNamespace(
        theta_x_degrees=theta_x, theta_y_degrees=theta_y, theta_z_degrees=theta_z,
        is_trial=True, is_calibrated=False, recorded_at=None, mounting_matrix=_P,
    )


def test_active_mounting_matrix_is_forwarded_to_the_orientation_view():
    QApplication.instance() or QApplication([])
    view = _FakeOrientationView()
    panel = SensorCalibrationPanel(orientation_view=view)

    panel.on_active_rotation_updated(_active(0.0, 0.0, 90.0))

    assert view.shown == [_P]
    assert panel.isAncestorOf(view)


def test_panel_works_without_orientation_view():
    QApplication.instance() or QApplication([])
    panel = SensorCalibrationPanel()
    panel.on_active_rotation_updated(_active(1.0, 2.0, 3.0))
    assert panel.spin_theta_z.value() == 3.0


def test_manual_procedure_help_is_folded_under_explicit_titles():
    from interface.widgets.collapsible_section.collapsible_section import CollapsibleSection

    QApplication.instance() or QApplication([])
    panel = SensorCalibrationPanel()
    panel.show()

    sections = panel.findChildren(CollapsibleSection)
    titles = [section.header.text() for section in sections]

    assert titles[0] == "Comment calibrer le capteur à la main, pas à pas"
    assert any("Convention" in title for title in titles)
    assert any("expérimentale" in title for title in titles)
    assert all(not section.is_expanded() for section in sections)

    sections[0].header.click()
    assert sections[0].is_expanded()
    assert "Reset to Default" in sections[0].findChild(QLabel).text()
