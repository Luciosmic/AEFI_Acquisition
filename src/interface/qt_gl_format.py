"""Qt OpenGL default format required by the 3D sensor view. See qt_gl_format_intention.md."""
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QSurfaceFormat


def vtk_default_format() -> QSurfaceFormat:
    """Desktop-GL 3.2 core format — same as pyvistaqt's (QVTKRenderWindowAdapter::defaultFormat)."""
    fmt = QSurfaceFormat()
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setVersion(3, 2)
    fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    fmt.setRedBufferSize(8)
    fmt.setGreenBufferSize(8)
    fmt.setBlueBufferSize(8)
    fmt.setDepthBufferSize(8)
    fmt.setAlphaBufferSize(8)
    fmt.setStencilBufferSize(0)
    fmt.setSamples(0)  # MSAA happens in VTK's FBOs, not the Qt context
    return fmt


def configure_qt_opengl() -> None:
    """Call before QApplication(): without it the 3D view composites black
    behind a splash window or in a floating dock."""
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QSurfaceFormat.setDefaultFormat(vtk_default_format())
