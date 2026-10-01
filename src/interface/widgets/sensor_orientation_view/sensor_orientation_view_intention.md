# sensor_orientation_view — Intention

## Rationale

While tuning the mounting angles by trial and error, the operator compares
the real sensor on the bench with what the software believes. Three numbers
do not show a mirrored or 180°-flipped mounting; a 3D cube does. This view
used to live in `external_modules/cube_visualizer` as a separate program
with its own angles, its own copy of the rotation convention and its own
buses: a second window, a second set of spinboxes to keep in sync by hand,
and a second definition of P that could drift from the reference one.
Living in the interface, fed with P computed by the domain, the cube can
only show the mounting actually applied to the readings.

## Responsibility

- Draw the sensor cube (one color per axis, green tape marker on each
  negative face), the sensor-frame axes (rotated by P) and the
  sources-frame axes (fixed).
- `show_mounting(matrix)`: redraw for a given P (3×3, rows; columns = sensor
  axes in the sources frame). The view knows nothing about angles or about
  the rotation convention.
- One row of camera-view buttons (3D, XY, XZ, YZ) above the 3D view.

## Design

- `SensorOrientationView(QWidget)`: buttons row + `pyvistaqt.QtInteractor`
  (both the Qt widget and the PyVista plotter API). Injected by the
  dashboard into the "Calibration capteur" panel.
- No text overlay: the host's spinboxes already show the angles.
- `configure_qt_opengl()` must run before `QApplication()`: the 3D view is a
  `QOpenGLWidget`, which composites **black** if the GL default format is
  set after the first top-level window exists (AEFI splash `StartupView`),
  or if it is moved to another top-level window (floating QtAds dock)
  without `AA_ShareOpenGLContexts` (observed on the bench 2026-10-01;
  pyvistaqt `rwi.py`, invariant 2).
- Renders under `QT_QPA_PLATFORM=offscreen` (tests).
