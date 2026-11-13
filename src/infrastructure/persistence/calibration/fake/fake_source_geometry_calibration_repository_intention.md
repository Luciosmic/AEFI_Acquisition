---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_source_geometry_calibration_repository` : Implement `ISourceGeometryCalibrationRepository` purely in memory: a list of entries."
code: ["[[src/infrastructure/persistence/calibration/fake/fake_source_geometry_calibration_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/test_bench_calibration/calibration_intention^^i-source-geometry-calibration-repository]]"]
double_de: "[[src/infrastructure/persistence/calibration/real_source_geometry_calibration_repository_intention]]"
---
# fake_source_geometry_calibration_repository — Intention

## Rationale

Application-layer tests for `SourceGeometryCalibrationService` must never
depend on the real JSON-file repository (file I/O, disk state). A pure
in-memory Fake implementing the exact same `ISourceGeometryCalibrationRepository`
contract lets those tests verify state (entries recorded) without any
infrastructure dependency, per this repo's Fake-over-Mock convention —
mirrors `FakeSensorCalibrationRepository`.

## Responsibility

- Implement `ISourceGeometryCalibrationRepository` purely in memory: a list
  of entries.
- Preserve the exact same contract as the Real implementation, including the
  append-only guarantee on `add()`.

## Design

- `_entries: List[SourceGeometryCalibrationEntry]` (append-only).
- `find_all()` returns a copy — callers must not be able to mutate internal
  state by mutating the returned list.
- No serialization, no file I/O — trivial pass-through storage.
