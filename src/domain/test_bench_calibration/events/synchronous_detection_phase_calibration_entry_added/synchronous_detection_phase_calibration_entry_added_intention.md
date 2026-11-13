---
type: evenement-de-domaine::solidai-ddd
tldr: "Signal that a new `SynchronousDetectionPhaseCalibrationEntry` was recorded in the calibration registry."
code: ["[[src/domain/test_bench_calibration/events/synchronous_detection_phase_calibration_entry_added/synchronous_detection_phase_calibration_entry_added.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
# synchronous_detection_phase_calibration_entry_added — Intention

## Rationale

When `Calibration.record_synchronous_detection_phase_entry(...)` adds a new
entry to the append-only registry, other parts of the system (the
synchronous detection presenter, notably) need to react — e.g. refresh the
displayed Delta_Phi lookup — without polling the aggregate or the
repository directly.

## Responsibility

- Signal that a new `SynchronousDetectionPhaseCalibrationEntry` was
  recorded in the calibration registry.
- Carry the full entry so subscribers do not need a follow-up read.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `entry: SynchronousDetectionPhaseCalibrationEntry` — the entry just
  recorded.
- Topic of publication: `"synchronousdetectionphasecalibrationentryadded"`.
