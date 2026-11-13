---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_hardware_component_repository` : In-memory, append-only implementation of `IHardwareComponentRepository`, filtered by kind like the Real one."
code: ["[[src/infrastructure/persistence/calibration/fake/fake_hardware_component_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/test_bench_configuration/bench_configuration_intention^^i-hardware-component-repository]]"]
double_de: "[[src/infrastructure/persistence/calibration/real_hardware_component_repository_intention]]"
---
# fake_hardware_component_repository — Intention

## Rationale

Application tests of `HardwareComponentService` and of the acquisition
snapshot would otherwise need the real JSON files.

## Responsibility

- In-memory, append-only implementation of `IHardwareComponentRepository`,
  filtered by kind like the Real one.

## Design

- Two plain lists. No failure modes simulated: the Real adapter swallows its
  load errors (returns empty) and has no quality-of-service the service
  depends on.
