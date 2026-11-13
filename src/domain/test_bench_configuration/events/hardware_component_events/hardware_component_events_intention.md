# hardware_component_events — Intention

## Rationale

When a component is characterized or mounted, its tab must refresh, and a
mounted board changes the hardware signature other calibrations rely on.
Without events the service would call those consumers directly.

## Responsibility

- `HardwareComponentCharacterized(entry)`: a characterization was recorded.
- `HardwareComponentMounted(kind, component_name, mounting_id)`: a component was declared
  mounted. Not emitted when it was already mounted (logged no-op).

## Design

- Frozen dataclasses inheriting `DomainEvent`, grouped in one module (the
  two facts of the same lifecycle change together).
- Topics `"hardwarecomponentcharacterized"`, `"hardwarecomponentmounted"`;
  consumers filter on the kind.
