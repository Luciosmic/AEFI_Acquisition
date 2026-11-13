---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_mechanical_transmission_calibration_repository` : Implement `IMechanicalTransmissionCalibrationRepository` in memory, append only, `find_all()` returning a copy."
code: ["[[src/infrastructure/persistence/calibration/fake/fake_mechanical_transmission_calibration_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/test_bench_calibration/calibration_intention^^i-mechanical-transmission-calibration-repository]]"]
double_de: "[[src/infrastructure/persistence/calibration/real_mechanical_transmission_calibration_repository_intention]]"
---
# fake_mechanical_transmission_calibration_repository — Intention

## Rationale

Application tests of the mechanical transmission service must not depend on
the JSON file (disk state). An in-memory Fake with the same append-only
contract lets them check state (entries recorded) — Fake-over-Mock, same as
`FakeSourceGeometryCalibrationRepository`.

## Responsibility

- Implement `IMechanicalTransmissionCalibrationRepository` in memory, append
  only, `find_all()` returning a copy.

## Design

- A plain list; no serialization. The Real's only failure mode (corrupt file
  read as empty) is the Fake's empty start.
