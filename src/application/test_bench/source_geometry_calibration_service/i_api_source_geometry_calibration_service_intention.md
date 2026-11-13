# i_api_source_geometry_calibration_service — Intention

## Rationale

Mirrors `IApiSensorCalibrationService`: gives
`SourceGeometryCalibrationPresenter` a stable inbound contract to depend on,
independent of the concrete service implementation.

## Responsibility

- `record_calibration(sphere_diameters_m, pairwise_distances_ext_m, resolution_m, k)`:
  the command exposed by the "Enregistrer calibration" button — also the
  same entry point the composition root uses once to seed the registry from
  the legacy device config JSON on first boot.
- `get_latest_calibration()`: the query used to populate the "last
  calibration" summary on panel load and after each successful record.

## Design

- Pure `ABC`, no state. Implemented by `SourceGeometryCalibrationService`.
- `resolution_m`/`k` default to the vernier caliper convention (0.02mm, k=2)
  already used throughout `aefi_device_config.json` — exposed as parameters
  rather than hardcoded so a future different instrument doesn't require a
  new method, but the panel v1 never overrides them (YAGNI until needed).
