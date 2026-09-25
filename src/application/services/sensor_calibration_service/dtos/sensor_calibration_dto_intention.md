# sensor_calibration_dto — Intention

## Rationale

Isolate the interface layer from `domain/` types (`SensorRotationAngles`,
`HardwareSignature`, the source geometry entry reference) used internally by
`SensorCalibrationService`. Only this object crosses the application ->
interface boundary for the sensor calibration feature — mirrors
`sphere_phases_dto`.

## Responsibility

- `SensorCalibrationDTO`: sensor identity (version, serial number), the 3
  calibrated angles (degrees) and the timestamp of the latest recorded entry
  that matches the current hardware signature and geometric configuration.
- `SensorIdentityDTO`: the sensor currently considered mounted, so the panel
  always shows which identity tags the calibrations, even before any sensor
  calibration exists for the current geometry.
- `ActiveSensorRotationDTO`: the mounting angles P (brings the sensor from
  the sources frame to its current mounting; measurement
  E_sensor = Pᵀ·E_sources; correction E_sources = P·E_sensor) currently applied to sensor readings, and where they come from: trial
  angles being tuned (`is_trial`, not persisted), else the latest calibration
  for the current hardware signature and source geometry (`is_calibrated`),
  else the ideal default angles.

## Design

- `@dataclass(frozen=True)` — immutable DTO, primitives only.
- `SensorCalibrationDTO` is built by `get_latest_calibration()`, which
  returns `None` instead of a DTO when no matching entry exists yet.
- `ActiveSensorRotationDTO` is built by `get_active_rotation()` and is never
  `None` — the ideal default angles always apply as a fallback.
