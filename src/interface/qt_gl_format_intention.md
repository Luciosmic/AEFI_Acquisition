# qt_gl_format — Intention

## Rationale

The 3D sensor view (pyvistaqt) composites black unless the Qt default
OpenGL format is set before the first top-level window exists, and the
startup splash is that first window. The format used to be fetched from
`pyvistaqt.rwi`, so setting it forced `main.py` to import pyvista and VTK
(seconds) before the splash could appear: the operator stared at nothing
for 4 s and could not tell a slow start from a crash.

## Responsibility

- `vtk_default_format()`: the QSurfaceFormat VTK needs (desktop GL 3.2 core).
- `configure_qt_opengl()`: share GL contexts and install that format; call
  before `QApplication()`.

## Design

- Copy of `pyvistaqt.rwi._default_format` (private), so this module imports
  only PySide6. `_tests/qt_gl_format_test.py` fails when the two diverge
  (skipped if the private attribute disappears).
