# fake_sensor_calibration_repository — Intention

## Rationale

Application-layer tests for `SensorCalibrationService` must never
depend on the real JSON-file repository (file I/O, disk state). A pure
in-memory Fake implementing the exact same `ISensorCalibrationRepository`
contract lets those tests verify state (entries recorded) without any
infrastructure dependency, per this repo's Fake-over-Mock convention —
mirrors `FakeSynchronousDetectionPhaseCalibrationRepository`.

## Responsibility

- Implement `ISensorCalibrationRepository` purely in memory: a list of
  entries.
- Preserve the exact same contract as the Real implementation, including the
  append-only guarantee on `add()`.

## Design

- `_entries: List[SensorCalibrationEntry]` (append-only).
- No serialization, no file I/O — trivial pass-through storage.
