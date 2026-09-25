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
