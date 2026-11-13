# source_geometry_calibration_dto — Intention

## Rationale

Isolate the interface layer from `domain/` types (`CaliperMeasurement`,
`SourceGeometryCalibrationEntry`) used internally by
`SourceGeometryCalibrationService`. Only this object crosses the
application -> interface boundary for the source geometry calibration
feature — mirrors `sensor_calibration_dto`.

## Responsibility

Carry the 10 calibrated values (4 sphere diameters + 6 extremity-to-extremity
distances, meters) with their GUM expanded uncertainty and shared coverage
factor `k`, plus the timestamp of the latest recorded entry.

## Design

- `@dataclass(frozen=True)` — immutable DTO, primitives only.
- `k` is a single shared field (not per-value) because every entry is built
  via `CaliperMeasurement.from_resolution(...)` with one shared `k` for the
  whole 10-value reading — see `source_geometry_calibration_service.py`.
- Built by `SourceGeometryCalibrationService.get_latest_calibration()`, which
  returns `None` instead of a DTO when the registry is empty.
