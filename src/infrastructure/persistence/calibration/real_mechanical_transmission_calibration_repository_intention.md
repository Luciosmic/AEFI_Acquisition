# real_mechanical_transmission_calibration_repository — Intention

## Rationale

The mechanical transmission registry must survive restarts and stay readable
(and hand-editable, since this pass has no UI to record a new setting)
outside the application. Same plain-JSON style as the other calibration
registries.

## Responsibility

- Implement `IMechanicalTransmissionCalibrationRepository` against
  `.aefi_acquisition/calibrations/mechanical_transmission_calibration.json`:
  `{"entries": [{entry_id, motor_mounting_id, stepper_driver_mounting_id,
  microsteps, driver_current_a, driver_peak_current_a,
  travel_per_motor_revolution_mm, recorded_at}]}`.
- Append only; a missing or corrupt file reads as empty (logged).

## Design

- Mirrors `RealSourceGeometryCalibrationRepository`: `_load` / `_write`,
  serialize/deserialize per entry, UUIDs as strings, ISO timestamps.
