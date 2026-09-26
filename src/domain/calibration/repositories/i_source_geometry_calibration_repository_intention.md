# i_source_geometry_calibration_repository — Intention

## Rationale

Defines the persistence contract for the source geometry calibration
registry, following the same Repository pattern as
`ISensorCalibrationRepository`: the domain declares WHAT to persist (an
append-only registry of entries), infrastructure decides HOW (a JSON file
today, see `RealSourceGeometryCalibrationRepository`).

## Responsibility

- `add(entry)`: append an entry — never overwrite or remove an existing one.
- `find_all()`: retrieve every entry. No hardware-signature filter (unlike
  the sensor calibration repository) — there is a single physical
  bench, so `SourceGeometryCalibrationService` filters nothing beyond
  picking the most recent by `recorded_at`. The composition root also reuses
  `find_all()` to detect an empty registry and seed it from the legacy
  `aefi_device_config.json` on first boot.

## Design

- **ABC placed in `domain/calibration/repositories/`**: domain/infrastructure
  boundary for this aggregate's persistence.
- Implemented by `RealSourceGeometryCalibrationRepository` (JSON,
  `.aefi_acquisition/calibrations/source_geometry_calibration.json`) and
  `FakeSourceGeometryCalibrationRepository` (in-memory), both in
  `infrastructure/persistence/calibration/`.
- The domain interface knows nothing of JSON or file paths — the domain
  stays pure.
