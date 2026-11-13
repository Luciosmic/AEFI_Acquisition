---
type: evenement-de-domaine::solidai-ddd
tldr: "Signal that a new `SensorCalibrationEntry` was recorded in the calibration registry."
code: ["[[src/domain/test_bench_calibration/events/sensor_calibration_entry_added/sensor_calibration_entry_added.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
# sensor_calibration_entry_added — Intention

## Rationale

When `Calibration.record_sensor_calibration_entry(...)` adds a new
entry to the append-only registry, other parts of the system (the sensor
angle calibration presenter, notably) need to react — e.g. refresh the
displayed "last calibration" label — without polling the aggregate or the
repository directly.

## Responsibility

- Signal that a new `SensorCalibrationEntry` was recorded in the
  calibration registry.
- Carry the full entry so subscribers do not need a follow-up read.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `entry: SensorCalibrationEntry` — the entry just recorded.
- Topic of publication: `"sensorcalibrationentryadded"`.
