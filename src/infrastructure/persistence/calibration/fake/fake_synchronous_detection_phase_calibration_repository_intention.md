---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_synchronous_detection_phase_calibration_repository` : Implement `ISynchronousDetectionPhaseCalibrationRepository` purely in memory: a list of entries plus a bool flag."
code: ["[[src/infrastructure/persistence/calibration/fake/fake_synchronous_detection_phase_calibration_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/test_bench_calibration/calibration_intention^^i-synchronous-detection-phase-calibration-repository]]"]
double_de: "[[src/infrastructure/persistence/calibration/real_synchronous_detection_phase_calibration_repository_intention]]"
---
# fake_synchronous_detection_phase_calibration_repository — Intention

## Rationale

Application-layer tests for `SynchronousDetectionService` must never
depend on the real JSON-file repository (file I/O, disk state). A pure
in-memory Fake implementing the exact same
`ISynchronousDetectionPhaseCalibrationRepository` contract lets those
tests verify state (entries recorded, compensation flag) without any
infrastructure dependency, per this repo's Fake-over-Mock convention.

## Responsibility

- Implement `ISynchronousDetectionPhaseCalibrationRepository` purely in
  memory: a list of entries plus a bool flag.
- Preserve the exact same contract as the Real implementation, including
  the append-only guarantee on `add()` and the `False` default for
  `load_compensation_enabled()` before anything has been saved.

## Design

- `_entries: List[SynchronousDetectionPhaseCalibrationEntry]` (append-only).
- `_compensation_enabled: bool = False`.
- No serialization, no file I/O — trivial pass-through storage.
