# hardware_component_name — Intention

## Rationale

A hardware component is referenced from other parts of the model — the
mounting log, the hardware signature that tags phase and sensor calibrations,
the acquisition export. In DDD those cross-references go through the
component's identity, never through a copy of its values. With a bare `str`,
nothing tells a reader (or the type checker) that a field *is* such a
reference rather than free text, and nothing stops a board name from being
passed where a sensor version is expected.

## Responsibility

- Name the identity type of a hardware component: its unique name.

## Design

- `NewType("HardwareComponentName", str)`, per the Typed Entity ID standard:
  zero runtime cost, stays a plain string in JSON, but every signature that
  takes or stores a component reference says so.
- Cast at the boundaries (UI input, persistence) with
  `HardwareComponentName(raw)`.
