---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `real_source_geometry_calibration_repository` : Implement `ISourceGeometryCalibrationRepository` against a single JSON file: `{\"entries\": [...]}`."
code: ["[[src/infrastructure/persistence/calibration/real_source_geometry_calibration_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/test_bench_calibration/calibration_intention^^i-source-geometry-calibration-repository]]"]
---
# real_source_geometry_calibration_repository — Intention

## Rationale

The source geometry calibration registry is, like the other calibration
registries in this bounded context, decided to be **append-only /
constructive**: a recorded entry must never be silently dropped or
rewritten — the history of what was measured on the bench, and when, must
remain reconstructible. Plain JSON on disk matches this codebase's config
persistence style and keeps the file human-inspectable for diagnostics.

## Responsibility

- Implement `ISourceGeometryCalibrationRepository` against a single JSON
  file: `{"entries": [...]}`.
- `add()`: load-append-write, never truncates or replaces the `entries`
  list.
- `find_all()`: deserialize every stored entry, preserving stored order.

## Design

- `DEFAULT_PATH = Path(".aefi_acquisition/calibrations/source_geometry_calibration.json")`
  — a separate file from the other calibration registries, overridable via
  constructor `storage_path` (tests must never write to
  `.aefi_acquisition/`).
- A missing or corrupt (invalid JSON) file is treated as `{"entries": []}` —
  never raises on read.
- Entry serialization:
  - `entry_id` -> `str(uuid)`
  - `sphere_diameters` / `pairwise_distances_ext` -> list of
    `{"value_m", "uncertainty_expanded_m", "k", "uniform_half_width_m"}` (one
    `CaliperMeasurement` per raw reading). A reading written before
    `uniform_half_width_m` existed is read back with its stored uncertainty
    unchanged and its half-width recovered by
    `CaliperMeasurement.from_uniform_expanded_uncertainty` (0.01 mm for the
    vernier default) — no migration, no error.
  - `recorded_at` -> `.isoformat()`
- `json.dump(..., indent=4)` for human-readability, matching the rest of the
  repo's JSON config files.
- Parent directories created on write (`mkdir(parents=True, exist_ok=True)`).
