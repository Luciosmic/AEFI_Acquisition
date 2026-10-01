# source_geometry_calibration_presenter — Intention

## Rationale

`SourceGeometryCalibrationPanel` (a tab of `CalibrationPanel`) needs a
Qt-facing adapter over `IApiSourceGeometryCalibrationService`, same as every
other panel in this codebase — mirrors `SensorCalibrationPresenter`.

## Responsibility

- `on_save_calibration_requested(sphere_diameters_m, pairwise_distances_ext_m)`:
  forward to `service.record_calibration(...)`, catch and report any error
  as a status message.
- `refresh_state()`: push `service.get_latest_calibration()` (DTO or `None`)
  to the panel via `latest_calibration_updated`.
- Subscribe to `SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC` at
  construction and call `refresh_state()` on it — `record_calibration()`
  publishes this event synchronously, so the panel refreshes automatically
  after every successful save.

## Design

- `QObject`, signals `latest_calibration_updated = Signal(object)` (DTO or
  `None`) and `status_message = Signal(str)`.
- `on_save_calibration_requested` is `@Slot(list, list)` — the panel emits
  plain Python lists of 4 and 6 floats (mm already converted to meters),
  not 10 separate float arguments.
- No domain logic in the `@Slot` — pure forwarding + try/except, same shape
  as `SensorCalibrationPresenter.on_save_calibration_requested`.
