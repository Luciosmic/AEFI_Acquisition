"""Tests CubeSensorWidget : composition root embarquable (contrôles + vue 3D)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cube_visualizer.interface.cube_sensor_widget import CubeSensorWidget


def _make_widget(**kwargs) -> CubeSensorWidget:
    QApplication.instance() or QApplication([])
    return CubeSensorWidget(**kwargs)


def test_3d_view_is_embedded_in_the_widget():
    w = _make_widget()
    assert w.isAncestorOf(w.adapter.widget)
    w.close()


def test_spinbox_edit_updates_service_orientation():
    w = _make_widget()
    w.spin_x.setValue(12.0)
    w._do_update()  # bypass the 150 ms debounce
    QApplication.processEvents()  # CommandBus is queued
    assert w.service.get_current_orientation().theta_x == 12.0
    w.close()


def test_show_orientation_drives_service_and_spinboxes():
    w = _make_widget()
    w.show_orientation(1.0, 2.0, 3.0)
    QApplication.processEvents()  # CommandBus then EventBus are queued
    QApplication.processEvents()
    dto = w.service.get_current_orientation()
    assert (dto.theta_x, dto.theta_y, dto.theta_z) == (1.0, 2.0, 3.0)
    assert w.spin_z.value() == 3.0
    w.close()


def test_angle_controls_can_be_hidden_for_a_host_owning_the_angles():
    w = _make_widget(angle_controls=False)
    w.show()
    assert not w.spin_x.isVisible()
    assert w.adapter.widget.isVisible()
    w.close()


def test_configure_qt_opengl_sets_shared_contexts_and_vtk_default_format():
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtGui import QSurfaceFormat
    from cube_visualizer.interface.cube_sensor_widget import configure_qt_opengl

    configure_qt_opengl()

    assert QCoreApplication.testAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    assert QSurfaceFormat.defaultFormat().version() == (3, 2)
