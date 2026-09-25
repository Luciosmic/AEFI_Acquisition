# active_sensor_rotation_changed — Intention

## Rationale

The rotation applied to every sensor sample (`TransformationService`)
must follow the calibration registry: a new sensor calibration, or a new
source geometry (for which no sensor calibration exists yet, so the ideal
angles apply), changes it. During trial-and-error tuning, trial angles (not
persisted) must also reach it live. Without this event, `TransformationService`
would either keep stale angles until restart or have to call
`SensorCalibrationService` directly (application service -> application
service, forbidden).

## Responsibility

- Carry the mounting rotation P now active (brings the sensor from the sources
  frame to its current mounting; readings corrected by `E_sources = P·E_sensor`;
  see `domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md`):
  the angles (with their convention), whether they come from a recorded
  calibration (`is_calibrated`) or are the ideal defaults, the calibration
  timestamp when there is one, and whether they are trial angles being tuned
  and not persisted (`is_trial`, default `False`).

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- Published by `SensorCalibrationService` (application layer), not minted by
  the `Calibration` aggregate: it is a derived fact ("which angles apply
  now"), not a registry transition. Same precedent as
  `SensorTransformationAnglesUpdated`, published by `TransformationService`.
- Topic: `"activesensorrotationchanged"`.
