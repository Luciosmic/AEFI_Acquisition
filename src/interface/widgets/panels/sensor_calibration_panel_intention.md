# sensor_calibration_panel — Intention

> 2026-09-25: the sensor identity group moved out of this tab — the sensor
> is declared, characterized (transduction gain) and mounted in the
> 'Capteur' component tab. This tab records only the mounting angles of the
> mounted sensor (`save_calibration_requested(theta_x, theta_y, theta_z)`)
> and shows the presenter's feedback via `set_status_message` (red when no
> sensor is mounted).

## Rationale

The sensor calibration procedure (thesis vault) needs one place where the
operator declares the mounted sensor, records its rotation angles and sees
which rotation is actually applied to the measurements. It is the
"Calibration capteur" tab of `CalibrationPanel`, which also replaces the
former `SensorTransformationPanel`: that panel held non-persisted angles
(hard-coded defaults) that were the only ones applied to sensor readings,
so recorded calibrations were never used.

## Responsibility

- Let the operator declare the mounted sensor (version, required; serial
  number, optional — blank = not provided) together with its calibration:
  this form is the single source of truth for sensor identity. Pre-filled
  with the sensor currently considered mounted.
- Let the operator tune the 3 mounting angles P by trial and error. P brings
  the sensor, aligned on the sources frame, to its current mounting; the
  sensor measures `E_sensor = Pᵀ·E_sources` and the readings are brought back
  to the sources frame by the transposed transform `E_sources = P·E_sensor`.
  The operator enters the mounting angles as they are, never negated: the
  software does the inversion. Every spinbox change is applied live to the
  readings (trial, not recorded), and the operator watches the signal brought
  back to the sources frame (excitation along X: `E_x^sources` max, the others
  min; along Y: `E_y^sources` max, the others min). There is no closed-form
  formula. "Enregistrer calibration" then records the angles as a new
  calibration entry. The procedure text shows the convention; its reference
  definition is
  `domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md`.
- "Reset to Default": restart the tuning from the ideal angles (as a trial).
- "Calibration automatique": disabled placeholder for a future automatic
  calibration service that will drive the same live preview with the same
  criterion.
- Display the last calibration entry recorded for the current hardware
  setup and sphere geometry (or an explicit "none yet" message).
- Display the active mounting ("Montage actif") — the angles P applied to
  sensor readings — and where it comes from (trial in progress, calibration date, or ideal
  default angles), and mirror its angles in the spinboxes.
- Show the active mounting in 3D, inside the panel (no other window): the
  cube follows the same active angles as the spinboxes, so there is a single
  set of angles on screen.
- No field-minimization logic here: the operator judges the signal; this UI
  forwards trial angles and captures the result with full traceability
  (hardware + geometry + date).

## Design

- `QWidget` (3x `QDoubleSpinBox` in a `QFormLayout`, explicit save button,
  read-only labels).
- `save_calibration_requested = Signal(str, object, float, float, float)`
  (version, serial or `None`, theta_x, theta_y, theta_z) — emitted only on
  click: it is an explicit record.
- `trial_rotation_requested = Signal(float, float, float)` — emitted on every
  spinbox `valueChanged` (live preview, not recorded);
  `reset_to_default_requested = Signal()` — emitted by "Reset to Default".
- `on_active_rotation_updated(dto)` sets the spinboxes inside
  `blockSignals(True/False)`, so mirroring the active rotation never starts a
  new trial.
- `orientation_view` (constructor, optional): any `QWidget` with
  `show_orientation(theta_x, theta_y, theta_z)`, placed to the right of the
  controls. The dashboard injects `CubeSensorWidget(angle_controls=False)`
  from `external_modules/cube_visualizer`; the panel never imports
  external modules.
- `on_latest_calibration_updated(dto)`: `dto` is `None` when no entry
  matches the current geometric configuration.
- `on_active_rotation_updated(dto)`: `ActiveSensorRotationDTO`, never `None`;
  mirrors the angles in the spinboxes and forwards them to
  `orientation_view` — the only path to the 3D view, so it always shows what
  is applied to the readings.
- `_tests/sensor_calibration_panel_test.py` covers the sync to
  `orientation_view` with a fake view.
