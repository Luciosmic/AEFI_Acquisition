"""Tests SensorOrientationView : vue 3D embarquable pilotée par la matrice P."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from interface.widgets.sensor_orientation_view.sensor_orientation_view import (
    SensorOrientationView,
    configure_qt_opengl,
)

_RZ90 = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def _make_view() -> SensorOrientationView:
    QApplication.instance() or QApplication([])
    return SensorOrientationView()


def test_3d_view_is_embedded_and_drawn_at_construction():
    view = _make_view()
    assert view.isAncestorOf(view.plotter)
    assert view.cube_actor is not None and view.marker_actor is not None
    view.close()


def test_show_mounting_redraws_cube_markers_and_both_axis_triads():
    view = _make_view()
    view.show_mounting(_RZ90)
    assert set(view.arrows_sensor) == {"x", "y", "z"}
    assert set(view.arrows_sources) == {"x", "y", "z"}
    view.close()


def test_one_row_of_four_camera_view_buttons():
    view = _make_view()
    labels = [b.text() for b in view.findChildren(QPushButton)]
    assert labels == ["Vue 3D", "Vue XY", "Vue XZ", "Vue YZ"]
    view.close()


def test_configure_qt_opengl_sets_shared_contexts_and_vtk_default_format():
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtGui import QSurfaceFormat

    configure_qt_opengl()

    assert QCoreApplication.testAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    assert QSurfaceFormat.defaultFormat().version() == (3, 2)
