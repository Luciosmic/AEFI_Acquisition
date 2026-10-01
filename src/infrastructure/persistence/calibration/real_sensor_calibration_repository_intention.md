# real_sensor_calibration_repository — Intention

## Rationale

The sensor calibration registry is, like the synchronous detection
phase calibration registry, decided to be **append-only / constructive**: a
recorded calibration entry must never be silently dropped or rewritten —
the history of what angles were measured, on which hardware and against
which sphere geometry, must remain reconstructible (recalibration after
reassembly is expected and must not erase prior entries). Plain JSON on disk
matches this codebase's config persistence style and keeps the file
human-inspectable for diagnostics.

## Responsibility

- Implement `ISensorCalibrationRepository` against a single JSON file:
  `{"entries": [...]}`. No `compensation_enabled`-style flag — sensor angle
  calibration is a pure registry, no active/inactive toggle.
- `add()`: load-append-write, never truncates or replaces the `entries`
  list.
- `find_by_hardware_signature()`: deserialize every stored entry and filter
  by VO equality against the requested signature, preserving stored order.

## Design

- `DEFAULT_PATH = Path(".aefi_acquisition/calibrations/sensor_calibration.json")`
  — a separate file from the synchronous detection phase registry (different
  aggregate concern, same aggregate root), overridable via constructor
  `storage_path` (tests must never write to `.aefi_acquisition/`).
- A missing or corrupt (invalid JSON) file is treated as `{"entries": []}` —
  never raises on read.
- Entry serialization:
  - `entry_id` -> `str(uuid)`
  - `hardware_signature` -> `hardware_signature_json` (shared with the phase
    registry; reads the pre-rename keys too)
  - `source_geometry_entry_id` -> `str(uuid)` of the source geometry entry
    (a reference, never a copy of the geometry values; entries written
    before 2026-09-25 were migrated once by matching their copied values)
  - `angles` -> `{"theta_x_degrees": ..., "theta_y_degrees": ..., "theta_z_degrees": ...,
    "convention": {"type", "order", "direction"}}` — an entry without a
    supported `convention` is rejected: no silent assumption about how its
    angles must be read.
- An unreadable entry (unsupported convention, missing field) is skipped
  with an ERROR naming its `entry_id` — it must not take the whole registry,
  and the application start, down with it.
  - `recorded_at` -> `.isoformat()`
- `json.dump(..., indent=4)` for human-readability, matching the rest of the
  repo's JSON config files.
- Parent directories created on write (`mkdir(parents=True, exist_ok=True)`).
