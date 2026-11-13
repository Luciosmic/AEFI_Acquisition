---
type: evenement-de-domaine::solidai-ddd
tldr: "Faits passés du banc : un composant a été caractérisé (`HardwareComponentCharacterized`) ou monté (`HardwareComponentMounted`)."
code: ["[[src/domain/test_bench_configuration/events/hardware_component_events/hardware_component_events.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_configuration/bench_configuration_intention]]"
---
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
