# sensor_calibration_presenter — Intention

## Rationale

`SensorCalibrationPanel` needs a Qt-facing adapter over
`IApiSensorCalibrationService`, same as every other panel in this
codebase — mirrors `SynchronousDetectionPresenter`.

## Responsibility

- `on_save_calibration_requested(sensor_version, sensor_serial_number, theta_x, theta_y, theta_z)`: forward to
  `service.record_calibration(...)`, catch and report any error as a status
  message (mirrors `on_save_calibration_point_requested`).
- `on_trial_rotation_requested(theta_x, theta_y, theta_z)`: forward to
  `service.preview_rotation(...)` — live trial-and-error tuning, applied to
  the readings without being recorded.
- `on_reset_to_default_requested()`: forward to `service.reset_to_default()`
  (ideal angles as the new trial).
- `refresh_state()`: push `service.get_current_sensor_identity()` via
  `sensor_identity_updated`, `service.get_latest_calibration()` (DTO or
  `None`) via `latest_calibration_updated`, and `service.get_active_rotation()`
  (never `None`) via `active_rotation_updated` — the rotation currently
  applied to sensor readings, calibrated or ideal default.
- Subscribe at construction to `SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC` and
  `ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC`, both calling `refresh_state()`.
  The second one also fires when a new source geometry is recorded from
  another tab (the active rotation falls back to the ideal angles), so the
  panel never shows a stale rotation.

## Design

- `QObject`, signals `latest_calibration_updated = Signal(object)`,
  `sensor_identity_updated = Signal(object)`, `active_rotation_updated =
  Signal(object)`, `status_message = Signal(str)`.
- A record publishes both events, so `refresh_state()` runs twice — harmless
  (idempotent reads), simpler than deduplicating.
- No domain logic in the `@Slot` — pure forwarding + try/except, same shape
  as `SynchronousDetectionPresenter.on_save_calibration_point_requested`.
- The trial slots have no try/except: preview/reset only build angles and
  publish, no expected failure to report. The resulting
  `ActiveSensorRotationChanged` refreshes the panel through `refresh_state()`.
