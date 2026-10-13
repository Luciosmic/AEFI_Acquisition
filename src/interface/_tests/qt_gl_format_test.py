"""qt_gl_format must stay identical to the format pyvistaqt installs."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QSurfaceFormat

from interface.qt_gl_format import configure_qt_opengl, vtk_default_format


def _fields(fmt: QSurfaceFormat):
    return (
        fmt.renderableType(), fmt.profile(), fmt.version(), fmt.swapBehavior(),
        fmt.redBufferSize(), fmt.greenBufferSize(), fmt.blueBufferSize(),
        fmt.depthBufferSize(), fmt.alphaBufferSize(), fmt.stencilBufferSize(), fmt.samples(),
    )


def test_vtk_default_format_matches_pyvistaqt():
    rwi = pytest.importorskip("pyvistaqt.rwi")
    reference = getattr(rwi, "_default_format", None)
    if reference is None:
        pytest.skip("pyvistaqt.rwi._default_format no longer exists")
    assert _fields(vtk_default_format()) == _fields(reference())


def test_configure_qt_opengl_sets_shared_contexts_and_default_format():
    configure_qt_opengl()
    assert QCoreApplication.testAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    assert QSurfaceFormat.defaultFormat().version() == (3, 2)
