# i_sensor_calibration_repository — Intention

## Rationale

Defines the persistence contract for the sensor calibration registry,
following the same Repository pattern as
`ISynchronousDetectionPhaseCalibrationRepository`: the domain declares WHAT
to persist (an append-only registry of entries), infrastructure decides HOW
(a JSON file today, see `RealSensorCalibrationRepository`).

## Responsibility

- `add(entry)`: append an entry to the registry — never overwrite or remove
  an existing one (constructive, append-only registry, same decision as the
  synchronous detection phase calibration registry).
- `find_all()`: every entry — the most recent one declares the currently
  mounted sensor (version + serial number); the registry is the source of
  truth for sensor identity.
- `find_by_hardware_signature(signature)`: retrieve all entries recorded for
  a given hardware signature. No geometry filter at the repository level —
  `SensorCalibrationService` filters by `source_geometry_entry_id`
  itself, mirroring how
  `SynchronousDetectionService._lookup_current_correction` already filters
  by frequency on top of the hardware-signature-filtered list.

## Design

- **ABC placed in `domain/calibration/repositories/`**: domain/infrastructure
  boundary for this aggregate's persistence.
- Implemented by `RealSensorCalibrationRepository` (JSON,
  `.aefi_acquisition/calibrations/sensor_calibration.json`) and
  `FakeSensorCalibrationRepository` (in-memory), both in
  `infrastructure/persistence/calibration/`.
- The domain interface knows nothing of JSON or file paths — the domain
  stays pure.
