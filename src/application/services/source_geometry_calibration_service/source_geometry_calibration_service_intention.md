# source_geometry_calibration_service — Intention

## Rationale

The 4-sphere source geometry (caliper-measured diameters + extremity-to-
extremity distances) had zero application-level traceability before this
feature: a hand-edited JSON block, no date, no history, GUM uncertainty
computed once by hand. Mirrors `SensorCalibrationService`'s shape
(record command + latest-calibration query on the same `Calibration`
aggregate) but adds a second responsibility: this service's registry is now
the **live source of truth** for the current source geometry, replacing
the direct JSON read `SensorCalibrationService` used to depend on. Other
calibrations reference it by identity (the entry id), never by copying its
values.

## Responsibility

- `record_calibration(sphere_diameters_m, pairwise_distances_ext_m, resolution_m, k)`:
  build 10 `CaliperMeasurement.from_resolution(...)` (GUM uncertainty
  computed automatically), call
  `Calibration.record_source_geometry_calibration_entry(...)`, persist the
  minted entry, publish the resulting domain event(s). Used both by the UI
  ("Enregistrer calibration" button) and, once, by the composition root to
  seed the registry from the legacy `aefi_device_config.json` on first boot
  — same method, no separate seeding code path (see
  `i_api_source_geometry_calibration_service_intention.md`).
- `get_latest_calibration()`: most recent entry (by `recorded_at`) across the
  whole registry (no filter dimension — a single physical bench), mapped to
  a DTO — `None` if the registry is empty.
- `get_current_entry_id()`: same "most recent" selection, returns its
  `entry_id` — what `main.py` passes into `SensorCalibrationService`, which
  stores it in each sensor calibration entry as `source_geometry_entry_id`.
  Raises `ValueError` if called before the registry has ever been seeded —
  defensive, should never trigger once the composition root's seed step runs.

## Design

- Constructor receives only `calibration_repository` and `event_bus` — no
  dependency on the legacy JSON reader. Seeding is composition-root plumbing
  (`main.py`), not a service concern: it just calls `record_calibration()`
  like any other caller, using values read via `GeometricConfigurationReader`.
- `record_calibration()` builds a **fresh** `Calibration()` instance (not
  `reconstitute`), same reasoning as `SensorCalibrationService` — no
  persisted flag to rehydrate, the aggregate is used purely for event-minting.
- Domain events published with `type(event).__name__.lower()` as topic, same
  convention as the other calibration services.
- `SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC = "sourcegeometrycalibrationentryadded"`
  exported as a module constant.
