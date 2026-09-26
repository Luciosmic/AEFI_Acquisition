# source_geometry_calibration_panel — Intention

## Rationale

The 4-sphere source geometry (caliper-measured diameters + pairwise
distances) had no UI entry point at all — only a hand-edited JSON. This
panel gives it the same recording UX as `SensorCalibrationPanel`, as a
second tab of the same `CalibrationPanel` dock (user request: group every
calibration in one place rather than one dock per calibration type).

## Responsibility

- Let the operator enter the 10 raw caliper readings (4 diameters + 6
  extremity-to-extremity distances) in millimeters — matching how a caliper
  is actually read — and record them as a new calibration entry.
- Display the last calibration entry recorded (10 values + GUM uncertainty +
  date), or an explicit "none yet" message.
- No uncertainty/resolution input in v1 — the service defaults (0.02mm
  vernier, k=2) match every value already hand-written in
  `aefi_device_config.json`; exposing them in the UI is deferred until a
  different instrument is actually used (YAGNI).

## Design

- `QWidget`, gabarit `sensor_calibration_panel.py` (QFormLayout per
  group, explicit save button, read-only summary label) — but a plain
  content widget, not registered as its own `Dashboard` dock: it is embedded
  as a tab inside `CalibrationPanel` (see `calibration_panel.py`).
- Entry in **millimeters** (`QDoubleSpinBox`, step 0.02mm = vernier
  resolution, decimals=3), converted to meters (`/1000`) only when emitting
  `save_calibration_requested = Signal(list, list)` — the service and every
  other domain/application layer works in meters, matching this codebase's
  existing unit convention; only the UI surfaces mm for operator usability.
- Field order matches `GeometricConfigurationSignature`
  (`_SPHERE_LABELS`/`_DISTANCE_LABELS` = S1..S4, D_S1_S2/D_S3_S4/D_S1_S3/
  D_S1_S4/D_S2_S3/D_S2_S4) so the emitted lists map 1:1 onto what
  `SourceGeometryCalibrationService.record_calibration` expects.
- `on_latest_calibration_updated(dto)` — `dto` is `None` when nothing has
  been recorded yet (should not happen once the composition root seeds the
  registry on first boot, but the panel doesn't assume that).
- No dedicated `_tests/` Qt tests — convention already followed by every
  other panel in this folder (presenters/services carry the tested logic).
