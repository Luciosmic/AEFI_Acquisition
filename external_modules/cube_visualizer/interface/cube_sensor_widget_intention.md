# cube_sensor_widget — Intention

## Rationale

The cube visualizer was wired inside a `QMainWindow` (`interface/main.py`),
so the only way to reuse it was to launch it as a separate process: a
second window, opened on its own default angles, unrelated to the mounting
being calibrated. The operator then had two sets of angle spinboxes to keep
in sync by hand. A self-contained `QWidget` composition root makes the
visualizer a component: the standalone launcher hosts it with its own
controls, and the "Calibration capteur" panel hosts only its 3D view, driven
by the active mounting angles.

## Responsibility

- Compose the module's layers (EventBus, CommandBus, PyVista adapter,
  `CubeVisualizerService`, presenter) and present them as one `QWidget`:
  angle controls on the left, and on the right one row of camera-view
  buttons above the 3D view.
- `show_orientation(theta_x, theta_y, theta_z)`: let a host drive the
  orientation (same path as a spinbox edit: presenter → service → render).
- `angle_controls=False`: hide the module's own angle spinboxes and reset,
  for a host that owns the angles (single source of truth). Camera-view
  buttons stay.
- Keep spinboxes and 3D view in sync through the module's `EventBus`
  (`ANGLES_CHANGED`), debouncing user edits (150 ms).

## Design

- `CubeSensorWidget(QWidget)`; `interface/main.py` only shows it in a
  window for standalone use.
- Angles follow the reference convention P = Rx·Ry·Rz
  (`from_euler('XYZ')`, see `src/domain/calibration/value_objects/
  rotation_convention/rotation_convention_intention.md`), so a host passes
  its mounting angles as they are.
- The host owns the widget's lifetime; the widget owns its buses, adapter,
  service and presenter.
- `configure_qt_opengl()` must run before `QApplication()` in a host that
  shows another top-level window first (AEFI splash `StartupView`) or that
  moves the widget to another top-level window (floating QtAds dock): the
  3D view is a `QOpenGLWidget`, which composites **black** if the GL default
  format is set after the first top-level window exists, or if it is
  reparented without `AA_ShareOpenGLContexts` (observed on the bench
  2026-10-01; pyvistaqt `rwi.py`, invariant 2).
