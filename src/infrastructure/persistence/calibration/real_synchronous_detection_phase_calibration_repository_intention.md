# real_synchronous_detection_phase_calibration_repository — Intention

## Rationale

The synchronous detection phase calibration registry is decided (with the
user) to be **append-only / constructive**: a calibration entry, once
recorded, must never be silently dropped or rewritten by a later save —
history of what was measured on which hardware setup must remain
reconstructible. Plain JSON on disk (no ORM, no database) matches the
rest of this codebase's config persistence style
(`hardware_config_resolution.py`, `UIConfigStore`) and keeps the file
human-inspectable for diagnostics.

## Responsibility

- Implement `ISynchronousDetectionPhaseCalibrationRepository` against a
  single JSON file: `{"entries": [...], "compensation_enabled": bool}`.
- `add()` : load-append-write, never truncates or replaces the `entries`
  list — this is the append-only guarantee the domain repository
  interface promises.
- `find_by_hardware_signature()` : deserialize every stored entry and
  filter by VO equality against the requested signature, preserving
  stored order.
- `load_compensation_enabled()` / `save_compensation_enabled()` : read or
  load-modify-write only the `compensation_enabled` key, leaving
  `entries` untouched.

## Design

- `DEFAULT_PATH = Path(".aefi_acquisition/calibrations/synchronous_detection_phase_calibration.json")`,
  overridable via constructor `storage_path` (used by tests to isolate
  from the real runtime directory — never write to `.aefi_acquisition/`
  from a test).
- A missing or corrupt (invalid JSON) file is treated as
  `{"entries": [], "compensation_enabled": False}` — never raises on
  read.
- Entry serialization:
  - `entry_id` -> `str(uuid)`
  - `hardware_signature` -> nested dict of its 4 fields
  - `points` -> list of `{"frequency_hz": ..., "delta_phi_degrees": ...}`
  - `recorded_at` -> `.isoformat()`
- Every write uses `json.dump(..., indent=4)` for human-readability,
  matching the rest of the repo's JSON config files.
- Parent directories are created on write (`mkdir(parents=True, exist_ok=True)`)
  since `.aefi_acquisition/configs/` may not exist yet on first run (the
  `ConfigBootstrapper` normally seeds it from `config_templates/`, but the
  repository must not depend on bootstrap order to be safe to use).
