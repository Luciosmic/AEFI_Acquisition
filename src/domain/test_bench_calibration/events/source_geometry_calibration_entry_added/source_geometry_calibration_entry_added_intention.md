# source_geometry_calibration_entry_added — Intention

## Rationale

When `Calibration.record_source_geometry_calibration_entry(...)` adds a new
entry to the append-only registry, other parts of the system (the source
geometry calibration presenter, notably) need to react — e.g. refresh the
displayed "last calibration" summary — without polling the aggregate or the
repository directly.

## Responsibility

- Signal that a new `SourceGeometryCalibrationEntry` was recorded in the
  calibration registry.
- Carry the full entry so subscribers do not need a follow-up read.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `entry: SourceGeometryCalibrationEntry` — the entry just recorded.
- Topic of publication: `"sourcegeometrycalibrationentryadded"`.
