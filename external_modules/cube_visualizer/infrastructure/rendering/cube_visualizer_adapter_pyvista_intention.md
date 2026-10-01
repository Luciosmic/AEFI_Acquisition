# cube_visualizer_adapter_pyvista — Intention

## Rationale

Without an embeddable renderer, the 3D view can only live in its own
PyVista window (`pv.Plotter().show()`). That window cannot be docked in the
acquisition dashboard, so the operator tuning the sensor mounting angles in
"Calibration capteur" has to juggle two top-level windows and the cube
cannot be placed next to the readings it explains. Embedding also lets a
host process drive the cube directly (no subprocess, no IPC), which is the
prerequisite for showing the active mounting live.

## Responsibility

- Implement `ICubeRenderer`: draw the colored cube, the sensor-frame axes
  (rotated) and the sources-frame axes (fixed) for a given rotation; reset
  the camera to a named view (`3d`, `xy`, `xz`, `yz`). Frame vocabulary:
  `src/domain/calibration/value_objects/rotation_convention/` ("lab" is
  not used).
- Expose the 3D view as a plain `QWidget` (`self.widget`) that any container
  (standalone window, QtAds dock) can place in its layout. The adapter never
  opens a window itself.
- React to `ANGLES_CHANGED` and `CAMERA_VIEW_CHANGED` from the module's
  `EventBus`.

## Design

- `self.widget = self.plotter = pyvistaqt.QtInteractor(parent_widget)`: the
  interactor is both the Qt widget and the PyVista plotter API. Dependency
  `pyvistaqt` (official PyVista Qt binding).
- The former separate PyVista window worked around a macOS OpenGL issue
  (`QtInteractor` not rendering); on the Windows bench `QtInteractor`
  renders, including under `QT_QPA_PLATFORM=offscreen` (tests).
- Initial render with the default domain angles happens in `__init__`: the
  widget is never shown empty.
- No angle/view text overlay in the scene: the angles are always shown by
  the host's spinboxes, a second display would only duplicate them.
